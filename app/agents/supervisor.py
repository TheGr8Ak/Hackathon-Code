"""
Supervisor Agent - Orchestrates all agents using LangGraph
"""
import logging
from typing import Dict, Any, TypedDict, Annotated, List
from datetime import datetime
from langgraph.graph import StateGraph, END
from app.agents.watchtower import WatchtowerAgent
from app.agents.quartermaster import QuartermasterAgent
from app.agents.press_secretary import PressSecretaryAgent


logger = logging.getLogger(__name__)


class SupervisorState(TypedDict):
    """State for supervisor workflow"""
    date: str
    forecast: Dict[str, Any]
    resource_actions: List[Dict[str, Any]]
    advisories_sent: List[Dict[str, Any]]
    daily_report: Dict[str, Any]


class SupervisorAgent:
    """Orchestrator agent that coordinates all other agents"""
    
    def __init__(self):
        self.watchtower = WatchtowerAgent()
        self.quartermaster = QuartermasterAgent()
        self.press_secretary = PressSecretaryAgent()
        self.workflow = self._build_workflow()
        logger.info("Supervisor agent initialized")
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(SupervisorState)
        
        # Add nodes
        workflow.add_node("forecast", self._run_forecast)
        workflow.add_node("analyze_resources", self._analyze_resources)
        workflow.add_node("execute_actions", self._execute_actions)
        workflow.add_node("send_advisories", self._send_advisories)
        workflow.add_node("generate_report", self._generate_report)
        
        # Define edges
        workflow.set_entry_point("forecast")
        workflow.add_edge("forecast", "analyze_resources")
        workflow.add_edge("analyze_resources", "execute_actions")
        workflow.add_edge("execute_actions", "send_advisories")
        workflow.add_edge("send_advisories", "generate_report")
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()
    
    async def _run_forecast(self, state: SupervisorState) -> SupervisorState:
        """Run Watchtower forecast"""
        logger.info(f"Running forecast for {state['date']}")
        
        # Use await instead of asyncio.run()
        forecast = await self.watchtower.forecast_patient_load(state['date'])
        
        state["forecast"] = forecast
        logger.info(f"Forecast complete: {forecast.get('predicted_load')} patients")
        
        return state
    
    async def _analyze_resources(self, state: SupervisorState) -> SupervisorState:
        """Run Quartermaster resource analysis"""
        logger.info("Analyzing resource needs")
        
        forecast = state.get("forecast", {})
        # Use await instead of asyncio.run()
        resource_analysis = await self.quartermaster.analyze_and_act(forecast)
        
        state["resource_actions"] = resource_analysis.get("actions_taken", [])
        logger.info(f"Resource analysis complete: {len(state['resource_actions'])} actions")
        
        return state
    
    async def _execute_actions(self, state: SupervisorState) -> SupervisorState:
        """Track executed actions (already executed by Quartermaster)"""
        logger.info(f"Actions execution tracked: {len(state.get('resource_actions', []))} actions")
        return state
    
    async def _send_advisories(self, state: SupervisorState) -> SupervisorState:
        """Send patient advisories if needed"""
        forecast = state.get("forecast", {})
        predicted_load = forecast.get("predicted_load", 0)
        drivers = forecast.get("drivers", {})
        
        advisories = []
        
        # Check if high load + pollution -> send advisory
        if predicted_load > 150 and drivers.get("pollution") == "HIGH":
            aqi = drivers.get("aqi", 0)
            # Use await instead of asyncio.run()
            advisory = await self.press_secretary.create_and_send_advisory(
                event_type="pollution_alert",
                severity="HIGH",
                details={
                    "aqi": aqi,
                    "predicted_load": predicted_load,
                    "hospital_name": "City Hospital"
                }
            )
            advisories.append(advisory)
            logger.info("Pollution advisory sent")
        
        # Check if epidemic alert
        if drivers.get("epidemic") == "ALERT":
            risk_score = drivers.get("risk_score", 0)
            # Use await instead of asyncio.run()
            advisory = await self.press_secretary.create_and_send_advisory(
                event_type="epidemic_alert",
                severity="CRITICAL",
                details={
                    "risk_score": risk_score,
                    "hospital_name": "City Hospital"
                }
            )
            advisories.append(advisory)
            logger.info("Epidemic advisory sent")
        
        # Check if surge warning needed
        if predicted_load > 200:
            # Use await instead of asyncio.run()
            advisory = await self.press_secretary.create_and_send_advisory(
                event_type="surge_warning",
                severity="MEDIUM",
                details={
                    "predicted_load": predicted_load,
                    "hospital_name": "City Hospital"
                }
            )
            advisories.append(advisory)
            logger.info("Surge warning sent")
        
        state["advisories_sent"] = advisories
        return state
    
    async def _generate_report(self, state: SupervisorState) -> SupervisorState:
        """Generate daily report"""
        report = {
            "date": state["date"],
            "forecast": state.get("forecast", {}),
            "actions_taken": len(state.get("resource_actions", [])),
            "advisories_sent": len(state.get("advisories_sent", [])),
            "summary": self._generate_summary(state),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        state["daily_report"] = report
        logger.info(f"Daily report generated for {state['date']}")
        return state
    
    def _generate_summary(self, state: SupervisorState) -> str:
        """Generate human-readable summary"""
        forecast = state.get("forecast", {})
        predicted_load = forecast.get("predicted_load", 0)
        actions_count = len(state.get("resource_actions", []))
        advisories_count = len(state.get("advisories_sent", []))
        
        summary = f"""
Daily Cycle Summary for {state['date']}:
- Predicted Patient Load: {predicted_load}
- Resource Actions Taken: {actions_count}
- Patient Advisories Sent: {advisories_count}
"""
        return summary.strip()
    
    async def run_daily_cycle(self, target_date: str) -> Dict[str, Any]:
        """
        Run complete daily cycle
        
        Args:
            target_date: Date string (YYYY-MM-DD)
        
        Returns:
            Final state with daily report
        """
        logger.info(f"Starting daily cycle for {target_date}")
        
        # Initialize state
        initial_state: SupervisorState = {
            "date": target_date,
            "forecast": {},
            "resource_actions": [],
            "advisories_sent": [],
            "daily_report": {}
        }
        
        # Use await instead of blocking invoke
        final_state = await self.workflow.ainvoke(initial_state)
        
        logger.info(f"Daily cycle complete for {target_date}")
        return final_state
