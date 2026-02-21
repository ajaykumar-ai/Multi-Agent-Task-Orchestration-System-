import asyncio
import os
from abc import ABC, abstractmethod
from typing import Any
from groq import Groq
from dotenv import load_dotenv

from models import Task, TaskStatus, AgentResult

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


async def call_llm(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
    )
    return response.choices[0].message.content.strip()


class Agent(ABC):
    name: str

    @abstractmethod
    async def run(self, task: Task) -> AgentResult:
        pass

    def emit(self, task: Task, message: str, data: Any = None):
        event = {"agent": self.name, "message": message}
        if data:
            event["data"] = data
        task.events.append(event)


class PlannerAgent(Agent):
    name = "Planner"

    async def run(self, task: Task) -> AgentResult:
        self.emit(task, f"Analyzing your request: '{task.prompt}'")
        prompt = f"""You are a task planner. Break the following user request into 3-5 clear, discrete research sub-tasks.
Return ONLY a JSON array of strings, no explanation.
Example: ["Research topic A", "Compare X and Y", "Analyze trade-offs"]

User request: {task.prompt}"""
        raw = await call_llm(prompt)
        import json, re
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        plan = json.loads(match.group()) if match else [task.prompt]
        self.emit(task, f"Created {len(plan)} sub-tasks", plan)
        task.plan = plan
        return AgentResult(agent=self.name, status="done", output=plan)


class ResearcherAgent(Agent):
    name = "Researcher"

    async def run(self, task: Task) -> AgentResult:
        research = {}
        for subtask in (task.plan or [task.prompt]):
            self.emit(task, f"Researching: {subtask}")
            prompt = f"""You are an expert researcher. Provide detailed, factual research on the following topic.
Topic: {subtask}
Original context: {task.prompt}
Provide 2-3 paragraphs of research."""
            result = await call_llm(prompt)
            research[subtask] = result
            self.emit(task, f"Completed research on: {subtask}")
        task.research = research
        return AgentResult(agent=self.name, status="done", output=research)


class WriterAgent(Agent):
    name = "Writer"

    async def run(self, task: Task) -> AgentResult:
        self.emit(task, "Synthesizing research into a draft report")
        research_text = "\n\n".join(f"### {t}\n{c}" for t, c in (task.research or {}).items())
        feedback_section = f"\n\nIMPORTANT - Reviewer feedback to address:\n{task.feedback}" if task.feedback else ""
        prompt = f"""You are a professional technical writer. Write a comprehensive, well-structured report.

Original request: {task.prompt}
{feedback_section}

Research material:
{research_text}

Write a professional report with an executive summary, clearly labeled sections, and a conclusion. Use markdown formatting."""
        draft = await call_llm(prompt)
        task.draft = draft
        self.emit(task, "Draft report completed")
        return AgentResult(agent=self.name, status="done", output=draft)


class ReviewerAgent(Agent):
    name = "Reviewer"

    async def run(self, task: Task) -> AgentResult:
        self.emit(task, "Reviewing draft for quality and completeness")
        prompt = f"""You are a critical quality reviewer. Review this report.

Original request: {task.prompt}

Draft:
{task.draft}

Respond in this EXACT format:
VERDICT: APPROVED or NEEDS_REVISION
FEEDBACK: <your detailed feedback>"""
        result = await call_llm(prompt)
        import re
        verdict_match = re.search(r'VERDICT:\s*(APPROVED|NEEDS_REVISION)', result)
        feedback_match = re.search(r'FEEDBACK:\s*(.+)', result, re.DOTALL)
        verdict = verdict_match.group(1) if verdict_match else "APPROVED"
        feedback = feedback_match.group(1).strip() if feedback_match else result
        self.emit(task, f"Review complete — {verdict}", {"verdict": verdict, "feedback": feedback})
        task.feedback = feedback
        return AgentResult(agent=self.name, status="approved" if verdict == "APPROVED" else "needs_revision", output=verdict, feedback=feedback)


class Orchestrator:
    def __init__(self, task: Task):
        self.task = task
        self.planner = PlannerAgent()
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()

    def _set_status(self, status: TaskStatus, agent_name: str):
        self.task.status = status
        self.task.current_agent = agent_name

    async def run(self):
        task = self.task
        try:
            self._set_status(TaskStatus.PLANNING, "Planner")
            task.agent_history.append(await self.planner.run(task))

            self._set_status(TaskStatus.RESEARCHING, "Researcher")
            task.agent_history.append(await self.researcher.run(task))

            self._set_status(TaskStatus.WRITING, "Writer")
            task.agent_history.append(await self.writer.run(task))

            for revision in range(2):
                self._set_status(TaskStatus.REVIEWING, "Reviewer")
                result = await self.reviewer.run(task)
                task.agent_history.append(result)
                if result.status == "approved":
                    break
                if revision < 1:
                    self._set_status(TaskStatus.REVISING, "Writer")
                    task.events.append({"agent": "Orchestrator", "message": "Sending draft back for revision"})
                    task.agent_history.append(await self.writer.run(task))

            task.final_report = task.draft
            task.status = TaskStatus.DONE
            task.current_agent = None
            task.events.append({"agent": "Orchestrator", "message": "Task completed successfully!"})

        except Exception as e:
            task.status = TaskStatus.ERROR
            task.error = str(e)
            task.events.append({"agent": "Orchestrator", "message": f"Error: {str(e)}"})