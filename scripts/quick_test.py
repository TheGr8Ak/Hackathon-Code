"""
Quick test script to verify system components
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.trust_boundaries import TrustBoundaryEngine
from app.core.kill_switch import KillSwitch
from app.core.approval_manager import ApprovalManager
from app.agents.watchtower import WatchtowerAgent
from app.agents.quartermaster import QuartermasterAgent

async def test_trust_boundaries():
    """Test trust boundaries engine"""
    print("Testing Trust Boundaries Engine...")
    engine = TrustBoundaryEngine()
    
    # Test low-risk purchase
    action = {
        "type": "PURCHASE_ORDER",
        "cost": 30000,
        "vendor": "vendor_a",
        "item_category": "medical_supplies"
    }
    result = engine.evaluate_action(action)
    print(f"  Low-risk purchase: {result['can_execute']} (Risk: {result['risk_level']})")
    assert result['can_execute'] == True, "Low-risk should execute autonomously"
    
    # Test high-risk purchase
    action = {
        "type": "PURCHASE_ORDER",
        "cost": 300000,
        "vendor": "vendor_a",
        "item_category": "medical_supplies"
    }
    result = engine.evaluate_action(action)
    print(f"  High-risk purchase: {result['can_execute']} (Risk: {result['risk_level']})")
    assert result['can_execute'] == False, "High-risk should require approval"
    
    print("✅ Trust boundaries test passed\n")

async def test_kill_switch():
    """Test kill switch"""
    print("Testing Kill Switch...")
    kill_switch = KillSwitch()
    
    status = kill_switch.is_system_active()
    print(f"  System active: {status}")
    
    print("✅ Kill switch test passed\n")

async def test_approval_manager():
    """Test approval manager"""
    print("Testing Approval Manager...")
    manager = ApprovalManager()
    
    action_id = manager.generate_action_id()
    print(f"  Generated action ID: {action_id}")
    
    manager.register_pending_action(action_id, {"type": "TEST"})
    decision = manager.get_approval_decision(action_id)
    print(f"  Initial decision: {decision['status']}")
    assert decision['status'] == 'PENDING', "Should be pending initially"
    
    manager.approve_action(action_id, "test_user", "Test approval")
    decision = manager.get_approval_decision(action_id)
    print(f"  After approval: {decision['status']}")
    assert decision['status'] == 'APPROVED', "Should be approved"
    
    print("✅ Approval manager test passed\n")

async def test_agents():
    """Test agent initialization"""
    print("Testing Agents...")
    
    watchtower = WatchtowerAgent()
    print(f"  ✅ Watchtower initialized: {watchtower.agent_name}")
    
    quartermaster = QuartermasterAgent()
    print(f"  ✅ Quartermaster initialized: {quartermaster.agent_name}")
    
    print("✅ Agents test passed\n")

async def main():
    """Run all tests"""
    print("=" * 50)
    print("Hospital AI System - Quick Test")
    print("=" * 50)
    print()
    
    try:
        await test_trust_boundaries()
        await test_kill_switch()
        await test_approval_manager()
        await test_agents()
        
        print("=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

