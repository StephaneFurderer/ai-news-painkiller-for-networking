import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from supabase import Client, create_client
from openai import OpenAI


load_dotenv()


def _create_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY/ANON_KEY env vars")
    return create_client(url, key)


class ChatStore:
    def __init__(self, client: Optional[Client] = None) -> None:
        self.client: Client = client or _create_client()
        self.llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Conversations
    def create_conversation(self, title: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        row = {"title": title, "user_id": user_id}
        res = self.client.table("conversations").insert(row).execute()
        return res.data[0]

    def archive_conversation(self, conversation_id: str) -> Dict[str, Any]:
        res = (
            self.client.table("conversations")
            .update({"status": "archived"})
            .eq("id", conversation_id)
            .execute()
        )
        return res.data[0] if res.data else {}

    def list_conversations(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        q = self.client.table("conversations").select("*").order("created_at", desc=True).limit(limit)
        if user_id:
            q = q.eq("user_id", user_id)
        res = q.execute()
        return res.data

    # Messages
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        row = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "user_id": user_id,
            "agent_name": agent_name,
            "metadata": metadata or {},
        }
        res = self.client.table("messages").insert(row).execute()
        return res.data[0]

    def get_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        before_iso: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        q = (
            self.client.table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=True)
            .limit(limit)
        )
        if before_iso:
            q = q.lt("created_at", before_iso)
        res = q.execute()
        return list(reversed(res.data))

    # State management
    def get_conversation_state(self, conversation_id: str) -> Dict[str, Any]:
        """Get the current state of a conversation"""
        res = self.client.table("conversations").select("state").eq("id", conversation_id).single().execute()
        return res.data.get("state", {}) if res.data else {}

    def update_conversation_state(self, conversation_id: str, state_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update conversation state (merges with existing state)"""
        current_state = self.get_conversation_state(conversation_id)
        new_state = {**current_state, **state_updates}
        
        res = self.client.table("conversations").update({"state": new_state}).eq("id", conversation_id).execute()
        return res.data[0] if res.data else {}

    # Summary management
    def get_conversation_summary(self, conversation_id: str) -> Optional[str]:
        res = self.client.table("conversations").select("summary").eq("id", conversation_id).single().execute()
        return res.data.get("summary") if res.data else None

    def update_running_summary(self, conversation_id: str, recent_turns: int = 200) -> Optional[str]:
        """Summarize recent messages and store to conversations.summary"""
        messages = self.get_messages(conversation_id, limit=recent_turns)
        if not messages:
            return None

        transcript = "\n".join([f"{m['role']}: {m['content']}" for m in messages])

        prompt = [
            {"role": "system", "content": "Summarize key facts, decisions, and user preferences. Be concise."},
            {"role": "user", "content": transcript[:12000]}
        ]
        res = self.llm.chat.completions.create(model="gpt-4o-mini", messages=prompt)
        summary = res.choices[0].message.content

        self.client.table("conversations").update({"summary": summary}).eq("id", conversation_id).execute()
        return summary

    # System prompts management
    def get_system_prompt(self, agent_name: str, version: Optional[str] = None) -> Optional[str]:
        """Get system prompt for agent. If version is None, gets current version."""
        if version:
            res = self.client.table("system_prompts").select("prompt").eq("agent_name", agent_name).eq("version", version).single().execute()
        else:
            res = self.client.table("system_prompts").select("prompt").eq("agent_name", agent_name).eq("is_current", True).single().execute()
        return res.data.get("prompt") if res.data else None

    def get_current_prompt_version(self, agent_name: str) -> Optional[str]:
        """Get the current version string for an agent's system prompt."""
        res = self.client.table("system_prompts").select("version").eq("agent_name", agent_name).eq("is_current", True).single().execute()
        return res.data.get("version") if res.data else None

    def set_system_prompt(self, agent_name: str, prompt: str, version: str, set_as_current: bool = True) -> Dict[str, Any]:
        """Set system prompt for agent. If set_as_current=True, marks as current and unmarks others."""
        # Insert new prompt
        res = self.client.table("system_prompts").insert({
            "agent_name": agent_name,
            "version": version,
            "prompt": prompt,
            "is_current": set_as_current
        }).execute()
        
        # If setting as current, unmark other versions
        if set_as_current:
            self.client.table("system_prompts").update({"is_current": False}).eq("agent_name", agent_name).neq("version", version).execute()
        
        return res.data[0] if res.data else {}

    # Context builder
    def build_context_for_agent(self, conversation_id: str, agent_name: str, recent_turns: int = 30) -> List[Dict[str, str]]:
        """Build context using stored system prompt for agent"""
        messages: List[Dict[str, str]] = []
        summary = self.get_conversation_summary(conversation_id)
        if summary:
            messages.append({"role": "system", "content": f"Conversation summary:\n{summary}"})
        
        # Get agent's system prompt from DB
        agent_prompt = self.get_system_prompt(agent_name)
        if agent_prompt:
            messages.append({"role": "system", "content": agent_prompt})
        
        recent = self.get_messages(conversation_id, limit=recent_turns)
        messages.extend({"role": m["role"], "content": m["content"]} for m in recent)
        return messages


class Coordinator:
    """Orchestrates agent workflows with completion tracking"""
    
    def __init__(self, store: ChatStore, client: OpenAI):
        self.store = store
        self.client = client

    def process_request(self, user_request: str, conversation_id: str) -> Dict[str, Any]:
        """Process user request through agent workflow"""
        # Add user message
        self.store.add_message(conversation_id, "user", user_request)
        
        # Reset conversation state
        self.store.update_conversation_state(conversation_id, {
            "status": "in_progress",
            "writer_complete": False,
            "reviewer_complete": False,
            "waiting_for_user": False,
            "user_request": user_request
        })
        
        # Step 1: Writer
        print("Starting Writer agent...")
        writer_result = self._call_writer(conversation_id, user_request)
        
        # Update state after writer
        self.store.update_conversation_state(conversation_id, {
            "writer_complete": True,
            "current_draft": writer_result,
            "needs_review": True
        })
        
        # Step 2: Reviewer
        print("Starting Reviewer agent...")
        reviewer_result = self._call_reviewer(conversation_id, writer_result)
        
        # Update state after reviewer
        self.store.update_conversation_state(conversation_id, {
            "reviewer_complete": True,
            "final_output": reviewer_result,
            "waiting_for_user": True,
            "status": "waiting_for_approval"
        })
        
        print("Workflow complete - waiting for user approval")
        return {
            "status": "waiting_for_approval",
            "final_output": reviewer_result,
            "conversation_id": conversation_id
        }

    def continue_after_user_input(self, conversation_id: str, user_response: str) -> Dict[str, Any]:
        """Continue conversation after user provides input"""
        state = self.store.get_conversation_state(conversation_id)
        
        if not state.get("waiting_for_user"):
            return {"error": "No conversation waiting for user input"}
        
        # Add user response
        self.store.add_message(conversation_id, "user", user_response)
        
        # Check if user wants to continue or is satisfied
        if self._is_satisfaction_response(user_response):
            # Mark as complete
            self.store.update_conversation_state(conversation_id, {
                "status": "completed",
                "waiting_for_user": False,
                "user_satisfied": True
            })
            return {
                "status": "completed",
                "message": "Conversation completed successfully"
            }
        else:
            # User wants changes - call Reviewer with feedback
            current_draft = state.get("current_draft", "")
            reviewer_result = self._call_reviewer_with_feedback(conversation_id, current_draft, user_response)
            
            # Update state
            self.store.update_conversation_state(conversation_id, {
                "final_output": reviewer_result,
                "waiting_for_user": True,
                "status": "waiting_for_approval"
            })
            
            return {
                "status": "waiting_for_approval",
                "final_output": reviewer_result,
                "conversation_id": conversation_id
            }

    def is_conversation_complete(self, conversation_id: str) -> bool:
        """Check if conversation is complete"""
        state = self.store.get_conversation_state(conversation_id)
        return (
            state.get("status") == "completed" or
            (state.get("reviewer_complete") and state.get("user_satisfied"))
        )

    def _call_writer(self, conversation_id: str, user_request: str) -> str:
        """Call Writer agent"""
        ctx = self.store.build_context_for_agent(conversation_id, "Writer", recent_turns=10)
        ctx.append({"role": "user", "content": user_request})
        
        response = self.client.chat.completions.create(model="gpt-4o-mini", messages=ctx)
        content = response.choices[0].message.content
        
        # Store message with version tracking
        version = self.store.get_current_prompt_version("Writer")
        self.store.add_message(
            conversation_id, "assistant", content, 
            agent_name="Writer",
            metadata={"model": "gpt-4o-mini", "system_prompt_version": version}
        )
        
        return content

    def _call_reviewer(self, conversation_id: str, draft: str) -> str:
        """Call Reviewer agent"""
        ctx = self.store.build_context_for_agent(conversation_id, "Reviewer", recent_turns=10)
        ctx.append({"role": "user", "content": f"Review this LinkedIn post: {draft}"})
        
        response = self.client.chat.completions.create(model="gpt-4o-mini", messages=ctx)
        content = response.choices[0].message.content
        
        # Store message with version tracking
        version = self.store.get_current_prompt_version("Reviewer")
        self.store.add_message(
            conversation_id, "assistant", content,
            agent_name="Reviewer", 
            metadata={"model": "gpt-4o-mini", "system_prompt_version": version}
        )
        
        return content

    def _call_reviewer_with_feedback(self, conversation_id: str, draft: str, feedback: str) -> str:
        """Call Reviewer with user feedback"""
        ctx = self.store.build_context_for_agent(conversation_id, "Reviewer", recent_turns=10)
        ctx.append({"role": "user", "content": f"Review this LinkedIn post: {draft}\n\nUser feedback: {feedback}"})
        
        response = self.client.chat.completions.create(model="gpt-4o-mini", messages=ctx)
        content = response.choices[0].message.content
        
        # Store message with version tracking
        version = self.store.get_current_prompt_version("Reviewer")
        self.store.add_message(
            conversation_id, "assistant", content,
            agent_name="Reviewer",
            metadata={"model": "gpt-4o-mini", "system_prompt_version": version}
        )
        
        return content

    def _is_satisfaction_response(self, response: str) -> bool:
        """Check if user response indicates satisfaction"""
        satisfaction_indicators = [
            "perfect", "great", "good", "looks good", "that works", 
            "i'm satisfied", "done", "complete", "thanks", "approve"
        ]
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in satisfaction_indicators)


