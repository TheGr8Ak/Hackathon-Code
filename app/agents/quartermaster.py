"""
Quartermaster Agent - Resource management and procurement
"""
import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from app.agents.level3_base_agent import Level3Agent

logger = logging.getLogger(__name__)


class QuartermasterAgent(Level3Agent):
    """Resource management agent - handles supplies, inventory, and staffing"""
    
    def __init__(self):
        super().__init__("Quartermaster")
        self.inventory_db = {}  # Mock inventory database
        self.supplier_db = {
            "vendor_a": {"name": "MedSupply Co", "contact": "+91-1234567890", "rating": 4.5},
            "vendor_b": {"name": "HealthCare Supplies", "contact": "+91-9876543210", "rating": 4.8},
            "vendor_c": {"name": "Medical Equipment Pro", "contact": "+91-5555555555", "rating": 4.2},
        }
        self.staff_db = {}  # Mock staff database
        
        logger.info("Quartermaster agent initialized")
    
    async def analyze_and_act(self, forecast: Dict) -> Dict:
        """
        Analyze forecast and take resource management actions
        
        Args:
            forecast: Forecast dict from Watchtower with predicted_load, drivers, etc.
        
        Returns:
            Dict with actions taken
        """
        predicted_load = forecast.get("predicted_load", 0)
        drivers = forecast.get("drivers", {})
        
        logger.info(f"Analyzing resource needs for predicted load: {predicted_load}")
        
        # Identify gaps
        supply_gaps = await self._identify_supply_gaps(predicted_load, drivers)
        staffing_gaps = await self._identify_staffing_gaps(predicted_load, drivers)
        
        actions_taken = []
        
        # Handle supply shortages
        for gap in supply_gaps:
            action_result = await self.handle_supply_shortage(gap, forecast)
            actions_taken.append(action_result)
        
        # Handle staffing shortages
        for gap in staffing_gaps:
            action_result = await self.handle_staffing_shortage(gap, forecast)
            actions_taken.append(action_result)
        
        return {
            "forecast_date": forecast.get("date"),
            "predicted_load": predicted_load,
            "supply_gaps_identified": len(supply_gaps),
            "staffing_gaps_identified": len(staffing_gaps),
            "actions_taken": actions_taken,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _identify_supply_gaps(self, predicted_load: int, drivers: Dict) -> List[Dict]:
        """Identify supply gaps based on predicted load"""
        gaps = []
        
        # Calculate required supplies (mock calculation)
        # In production, this would query inventory and calculate based on historical usage
        
        # Example: Oxygen cylinders
        current_oxygen = self.inventory_db.get("oxygen_cylinders", {}).get("quantity", 50)
        required_oxygen = predicted_load * 0.3  # 0.3 cylinders per patient
        
        if current_oxygen < required_oxygen:
            gaps.append({
                "item": "oxygen_cylinders",
                "category": "medical_supplies",
                "current": current_oxygen,
                "required": int(required_oxygen),
                "shortage": int(required_oxygen - current_oxygen),
                "unit": "cylinders"
            })
        
        # Example: IV fluids
        current_iv = self.inventory_db.get("iv_fluids", {}).get("quantity", 200)
        required_iv = predicted_load * 2  # 2 units per patient
        
        if current_iv < required_iv:
            gaps.append({
                "item": "iv_fluids",
                "category": "consumables",
                "current": current_iv,
                "required": int(required_iv),
                "shortage": int(required_iv - current_iv),
                "unit": "units"
            })
        
        # Example: PPE kits
        current_ppe = self.inventory_db.get("ppe_kits", {}).get("quantity", 100)
        required_ppe = predicted_load * 1.5  # 1.5 kits per patient
        
        if current_ppe < required_ppe:
            gaps.append({
                "item": "ppe_kits",
                "category": "consumables",
                "current": current_ppe,
                "required": int(required_ppe),
                "shortage": int(required_ppe - current_ppe),
                "unit": "kits"
            })
        
        return gaps
    
    async def _identify_staffing_gaps(self, predicted_load: int, drivers: Dict) -> List[Dict]:
        """Identify staffing gaps based on predicted load"""
        gaps = []
        
        # Calculate required staff (mock calculation)
        # In production, this would check schedules and calculate based on patient-to-staff ratios
        
        # Example: Nurses
        current_nurses = self.staff_db.get("nurses_available", 20)
        required_nurses = predicted_load * 0.5  # 0.5 nurses per patient
        
        if current_nurses < required_nurses:
            gaps.append({
                "role": "nurses",
                "current": current_nurses,
                "required": int(required_nurses),
                "shortage": int(required_nurses - current_nurses),
                "department": "general"
            })
        
        # Example: Doctors
        current_doctors = self.staff_db.get("doctors_available", 8)
        required_doctors = predicted_load * 0.1  # 0.1 doctors per patient
        
        if current_doctors < required_doctors:
            gaps.append({
                "role": "doctors",
                "current": current_doctors,
                "required": int(required_doctors),
                "shortage": int(required_doctors - current_doctors),
                "department": "general"
            })
        
        return gaps
    
    async def handle_supply_shortage(self, gap: Dict, forecast: Dict) -> Dict:
        """Handle a supply shortage by creating purchase order"""
        
        item = gap.get("item")
        shortage = gap.get("shortage", 0)
        category = gap.get("category", "unknown")
        
        # Get supplier info (mock)
        supplier = self._get_supplier_for_item(item, category)
        
        if not supplier:
            logger.warning(f"No supplier found for {item}")
            return {
                "status": "FAILED",
                "reason": "No supplier available",
                "gap": gap
            }
        
        # Calculate cost (mock pricing)
        unit_price = self._get_item_price(item)
        total_cost = unit_price * shortage
        
        # Construct purchase order action
        action = {
            "type": "PURCHASE_ORDER",
            "item": item,
            "item_category": category,
            "quantity": shortage,
            "unit": gap.get("unit", "units"),
            "cost": total_cost,
            "vendor": supplier["name"],
            "vendor_id": supplier.get("id", "vendor_a"),
            "reasoning": f"Supply gap identified: {shortage} {gap.get('unit')} of {item} needed for predicted load of {forecast.get('predicted_load')} patients",
            "urgency": "HIGH" if shortage > 50 else "MEDIUM"
        }
        
        # Execute through Level 3 framework (will check trust boundaries)
        result = await self.propose_and_execute(action)
        return result
    
    async def handle_staffing_shortage(self, gap: Dict, forecast: Dict) -> Dict:
        """Handle a staffing shortage by creating staffing change action"""
        
        role = gap.get("role")
        shortage = gap.get("shortage", 0)
        department = gap.get("department", "general")
        
        # Calculate overtime hours needed (mock)
        overtime_hours = shortage * 8  # 8 hours per staff member
        
        # Construct staffing change action
        action = {
            "type": "STAFFING_CHANGE",
            "role": role,
            "department": department,
            "shortage": shortage,
            "overtime_hours": overtime_hours,
            "temp_staff_count": shortage,
            "reasoning": f"Staffing gap identified: {shortage} {role} needed for predicted load of {forecast.get('predicted_load')} patients",
            "urgency": "HIGH" if shortage > 5 else "MEDIUM"
        }
        
        # Execute through Level 3 framework
        result = await self.propose_and_execute(action)
        return result
    
    def _get_supplier_for_item(self, item: str, category: str) -> Dict:
        """Get supplier information for an item (mock)"""
        # Simple mapping logic
        if "oxygen" in item.lower():
            return {"id": "vendor_a", "name": "MedSupply Co", "contact": "+91-1234567890"}
        elif "iv" in item.lower() or "fluid" in item.lower():
            return {"id": "vendor_b", "name": "HealthCare Supplies", "contact": "+91-9876543210"}
        else:
            return {"id": "vendor_c", "name": "Medical Equipment Pro", "contact": "+91-5555555555"}
    
    def _get_item_price(self, item: str) -> float:
        """Get unit price for an item (mock pricing)"""
        prices = {
            "oxygen_cylinders": 5000.0,
            "iv_fluids": 200.0,
            "ppe_kits": 500.0
        }
        return prices.get(item, 1000.0)
    
    async def execute_action(self, action: Dict) -> Any:
        """Execute the action (purchase order or staffing change)"""
        action_type = action.get("type")
        
        if action_type == "PURCHASE_ORDER":
            return await self._execute_purchase_order(action)
        elif action_type == "STAFFING_CHANGE":
            return await self._execute_staffing_change(action)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    async def _execute_purchase_order(self, action: Dict) -> Dict:
        """Execute a purchase order"""
        item = action.get("item")
        quantity = action.get("quantity", 0)
        vendor_id = action.get("vendor_id")
        cost = action.get("cost", 0)
        
        logger.info(f"Placing purchase order: {quantity} {item} from {vendor_id} (₹{cost})")
        
        # Mock supplier API call
        order_id = f"PO_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Simulate API delay
        await asyncio.sleep(0.5)
        
        # Update inventory (mock)
        if item not in self.inventory_db:
            self.inventory_db[item] = {"quantity": 0}
        self.inventory_db[item]["quantity"] += quantity
        
        return {
            "order_id": order_id,
            "status": "PLACED",
            "item": item,
            "quantity": quantity,
            "cost": cost,
            "vendor": vendor_id,
            "estimated_delivery": (datetime.utcnow().timestamp() + 86400),  # 24 hours
            "confirmation": f"Order {order_id} placed successfully with {vendor_id}"
        }
    
    async def _execute_staffing_change(self, action: Dict) -> Dict:
        """Execute a staffing change"""
        role = action.get("role")
        overtime_hours = action.get("overtime_hours", 0)
        temp_staff_count = action.get("temp_staff_count", 0)
        
        logger.info(f"Executing staffing change: {overtime_hours}h overtime, {temp_staff_count} temp staff for {role}")
        
        # Mock HR system update
        change_id = f"STAFF_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Simulate processing delay
        await asyncio.sleep(0.3)
        
        # Update staff database (mock)
        if role not in self.staff_db:
            self.staff_db[role] = {"available": 0}
        self.staff_db[role]["available"] += temp_staff_count
        
        return {
            "change_id": change_id,
            "status": "SCHEDULED",
            "role": role,
            "overtime_hours": overtime_hours,
            "temp_staff_count": temp_staff_count,
            "confirmation": f"Staffing change {change_id} scheduled successfully"
        }
    
    async def verify_outcome(self, action: Dict, result: Dict) -> Dict:
        """Verify if action achieved desired outcome"""
        action_type = action.get("type")
        
        if action_type == "PURCHASE_ORDER":
            # Check if order was delivered
            order_id = result.get("order_id")
            # In production, check supplier API or delivery tracking
            # For now, assume success if order_id exists
            if order_id:
                return {
                    "success": True,
                    "notes": f"Purchase order {order_id} verified - items received",
                    "verified_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "notes": "Purchase order verification failed - no order ID",
                    "verified_at": datetime.utcnow().isoformat()
                }
        
        elif action_type == "STAFFING_CHANGE":
            # Check if staffing shortage was resolved
            change_id = result.get("change_id")
            if change_id:
                return {
                    "success": True,
                    "notes": f"Staffing change {change_id} verified - staff deployed",
                    "verified_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "notes": "Staffing change verification failed",
                    "verified_at": datetime.utcnow().isoformat()
                }
        
        return {
            "success": True,
            "notes": "Action verification completed",
            "verified_at": datetime.utcnow().isoformat()
        }
