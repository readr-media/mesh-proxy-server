#!/usr/bin/env python3
"""
通知調試工具
用於診斷 "cannot get memberId" 錯誤
"""

import os
from typing import List, Dict, Any, Optional

class NotifyDebugger:
    """通知調試器，用於診斷成員 ID 問題"""
    
    @staticmethod
    def analyze_notification_data(notifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析通知資料，找出問題所在"""
        analysis = {
            "total_notifications": len(notifications),
            "payment_notifications": 0,
            "regular_notifications": 0,
            "unique_member_ids": set(),
            "problematic_notifications": [],
            "aggregate_notifications": 0,
            "single_notifications": 0
        }
        
        for i, notify in enumerate(notifications):
            action = notify.get('action', '')
            
            # 統計支付通知
            if action in ['payment_success', 'payment_failed']:  # 假設這些是支付通知
                analysis["payment_notifications"] += 1
                continue
            
            analysis["regular_notifications"] += 1
            
            # 分析 from 字段
            from_field = notify.get('from', None)
            aggregate = notify.get('aggregate', False)
            
            if aggregate:
                analysis["aggregate_notifications"] += 1
                if isinstance(from_field, list):
                    analysis["unique_member_ids"].update(from_field)
                else:
                    analysis["problematic_notifications"].append({
                        "index": i,
                        "issue": "aggregate=True but from is not a list",
                        "from_field": from_field,
                        "notify": notify
                    })
            else:
                analysis["single_notifications"] += 1
                if isinstance(from_field, str):
                    analysis["unique_member_ids"].add(from_field)
                else:
                    analysis["problematic_notifications"].append({
                        "index": i,
                        "issue": "aggregate=False but from is not a string",
                        "from_field": from_field,
                        "notify": notify
                    })
        
        analysis["unique_member_ids"] = list(analysis["unique_member_ids"])
        analysis["unique_member_count"] = len(analysis["unique_member_ids"])
        
        return analysis
    
    @staticmethod
    def debug_member_lookup(member_id: str, member_table: Dict[str, Any], 
                           notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """調試特定成員 ID 的查找問題"""
        debug_info = {
            "member_id": member_id,
            "member_found": member_id in member_table,
            "member_table_keys": list(member_table.keys()),
            "member_table_size": len(member_table),
            "notification_context": notification_data
        }
        
        if member_id in member_table:
            debug_info["member_data"] = member_table[member_id]
        else:
            debug_info["similar_ids"] = [
                key for key in member_table.keys() 
                if str(key).startswith(str(member_id)[:5]) or str(member_id).startswith(str(key)[:5])
            ]
        
        return debug_info
    
    @staticmethod
    def suggest_solutions(analysis: Dict[str, Any]) -> List[str]:
        """根據分析結果提供解決建議"""
        suggestions = []
        
        if analysis["problematic_notifications"]:
            suggestions.append("發現資料格式問題：")
            for problem in analysis["problematic_notifications"]:
                suggestions.append(f"  - 通知 {problem['index']}: {problem['issue']}")
            suggestions.append("建議檢查通知資料的格式是否正確")
        
        if analysis["unique_member_count"] > 100:
            suggestions.append("成員 ID 數量過多，可能影響 GQL 查詢效能")
            suggestions.append("建議分批查詢或使用快取機制")
        
        if analysis["unique_member_count"] == 0 and analysis["regular_notifications"] > 0:
            suggestions.append("沒有找到有效的成員 ID，檢查通知資料的 'from' 字段")
        
        return suggestions
    
    @staticmethod
    def create_mock_member(member_id: str) -> Dict[str, Any]:
        """創建一個模擬成員資料，用於處理缺失的成員"""
        return {
            "id": member_id,
            "name": f"Unknown Member ({member_id})",
            "nickname": f"Unknown_{member_id}",
            "customId": f"unknown_{member_id}",
            "avatar": None,
            "is_active": False,
            "_debug": "This is a mock member created for missing data"
        }

# 便捷函數
def debug_notification_issue(member_id: str, member_table: Dict[str, Any], 
                           notification_data: Dict[str, Any]) -> None:
    """調試通知問題的便捷函數"""
    debugger = NotifyDebugger()
    debug_info = debugger.debug_member_lookup(member_id, member_table, notification_data)
    
    print(f"🔍 調試成員 ID: {member_id}")
    print(f"   成員是否找到: {debug_info['member_found']}")
    print(f"   成員表大小: {debug_info['member_table_size']}")
    
    if not debug_info['member_found']:
        print(f"   相似 ID: {debug_info['similar_ids']}")
        print(f"   建議創建模擬成員")
    
    return debug_info

def analyze_notifications(notifications: List[Dict[str, Any]]) -> None:
    """分析通知資料的便捷函數"""
    debugger = NotifyDebugger()
    analysis = debugger.analyze_notification_data(notifications)
    
    print("📊 通知資料分析:")
    print(f"   總通知數: {analysis['total_notifications']}")
    print(f"   支付通知: {analysis['payment_notifications']}")
    print(f"   一般通知: {analysis['regular_notifications']}")
    print(f"   聚合通知: {analysis['aggregate_notifications']}")
    print(f"   單一通知: {analysis['single_notifications']}")
    print(f"   唯一成員 ID 數: {analysis['unique_member_count']}")
    
    if analysis['problematic_notifications']:
        print(f"   ⚠️ 發現 {len(analysis['problematic_notifications'])} 個問題通知")
    
    suggestions = debugger.suggest_solutions(analysis)
    if suggestions:
        print("💡 建議:")
        for suggestion in suggestions:
            print(f"   {suggestion}")
    
    return analysis 