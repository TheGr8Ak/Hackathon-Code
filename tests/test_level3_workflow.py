"""
Integration tests for Level 3 workflow
"""
import pytest
import asyncio
from datetime import datetime
from app.agents.watchtower import WatchtowerAgent
from app.agents.quartermaster import QuartermasterAgent
from app.core.trust_boundaries import TrustBoundaryEngine
from app.core.kill_switch import KillSwitch
from app.core.approval_manager import ApprovalManager


@pytest.mark.asyncio
async def test_low_risk_purchase_auto_executes():
    """Test that low-risk purchase executes autonomously"""
    engine = TrustBoundaryEngine()
    
    action = {
        "type": "PURCHASE_ORDER",
        "cost": 30000,  # Below ₹50k threshold
        "vendor": "vendor_a",
        "item_category": "medical_supplies"
    }
    
    evaluation = engine.evaluate_action(action)
    assert evaluation["can_execute"] == True
    assert evaluation["risk_level"] == "LOW"
    assert evaluation["execution_type"] == "AUTONOMOUS"


@pytest.mark.asyncio
async def test_high_risk_purchase_requires_approval():
    """Test that high-risk purchase requires approval"""
    engine = TrustBoundaryEngine()
    
    action = {
        "type": "PURCHASE_ORDER",
        "cost": 300000,  # Above ₹2L threshold
        "vendor": "vendor_a",
        "item_category": "medical_supplies"
    }
    
    evaluation = engine.evaluate_action(action)
    assert evaluation["can_execute"] == False
    assert evaluation["risk_level"] in ["HIGH", "CRITICAL"]
    assert evaluation["execution_type"] == "PENDING"
    assert len(evaluation["required_approvals"]) > 0


@pytest.mark.asyncio
async def test_kill_switch_blocks_actions():
    """Test that kill switch blocks all actions"""
    kill_switch = KillSwitch()
    engine = TrustBoundaryEngine()
    
    # Activate kill switch
    kill_switch.activate_kill_switch("Test", "test_user")
    
    # Update trust boundaries config
    engine.config["global_rules"]["kill_switch_active"] = True
    
    action = {
        "type": "PURCHASE_ORDER",
        "cost": 10000,  # Low risk
        "vendor": "vendor_a",
        "item_category": "medical_supplies"
    }
    
    evaluation = engine.evaluate_action(action)
    assert evaluation["can_execute"] == False
    assert "kill switch" in evaluation["reasons"][0].lower()
    
    # Cleanup
    kill_switch.reactivate_system("test_user", "Test cleanup")
    engine.config["global_rules"]["kill_switch_active"] = False


@pytest.mark.asyncio
async def test_approval_workflow():
    """Test approval workflow"""
    manager = ApprovalManager()
    
    action_id = manager.generate_action_id()
    manager.register_pending_action(action_id, {"type": "TEST"})
    
    # Initially pending
    decision = manager.get_approval_decision(action_id)
    assert decision["status"] == "PENDING"
    
    # Approve
    manager.approve_action(action_id, "test_user", "Test approval")
    decision = manager.get_approval_decision(action_id)
    assert decision["status"] == "APPROVED"
    assert decision["approved_by"] == "test_user"


@pytest.mark.asyncio
async def test_watchtower_forecast():
    """Test Watchtower forecasting"""
    agent = WatchtowerAgent()
    
    forecast_date = datetime.now().strftime("%Y-%m-%d")
    forecast = await agent.forecast_patient_load(forecast_date)
    
    assert "predicted_load" in forecast
    assert "confidence" in forecast
    assert "drivers" in forecast
    assert forecast["predicted_load"] > 0


@pytest.mark.asyncio
async def test_quartermaster_resource_analysis():
    """Test Quartermaster resource analysis"""
    agent = QuartermasterAgent()
    
    forecast = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "predicted_load": 150,
        "drivers": {"pollution": "HIGH", "aqi": 200}
    }
    
    result = await agent.analyze_and_act(forecast)
    
    assert "forecast_date" in result
    assert "actions_taken" in result
    assert isinstance(result["actions_taken"], list)


@pytest.mark.asyncio
async def test_full_daily_cycle():
    """Test full daily cycle (supervisor)"""
    from app.agents.supervisor import SupervisorAgent
    
    supervisor = SupervisorAgent()
    target_date = datetime.now().strftime("%Y-%m-%d")
    
    result = await supervisor.run_daily_cycle(target_date)
    
    assert "daily_report" in result
    assert "forecast" in result
    assert result["date"] == target_date

