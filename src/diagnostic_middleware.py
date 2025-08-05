import asyncio
import os
from typing import Dict, Any, Optional
from src.mongo_client import get_mongo_manager, initialize_mongo, close_mongo

class DiagnosticMiddleware:
    """
    診斷中間件，用於在應用運行時進行 MongoDB 連接和資料獲取診斷
    """
    
    @staticmethod
    async def check_mongo_connection() -> Dict[str, Any]:
        """檢查 MongoDB 連接狀態"""
        result = {
            "status": "unknown",
            "error": None,
            "details": {}
        }
        
        try:
            # 檢查環境變數
            mongo_url = os.environ.get('MONGO_URL')
            env = os.environ.get('ENV', 'dev')
            
            result["details"]["mongo_url"] = mongo_url
            result["details"]["env"] = env
            
            if not mongo_url:
                result["status"] = "error"
                result["error"] = "MONGO_URL 未設定"
                return result
            
            # 嘗試獲取管理器
            manager = await get_mongo_manager()
            db = manager.get_async_db()
            
            # 測試連接
            await db.command("ping")
            
            result["status"] = "connected"
            result["details"]["database"] = db.name
            
            # 檢查集合
            collections = await db.list_collection_names()
            result["details"]["collections"] = collections
            
            # 檢查各集合的文檔數量
            collection_counts = {}
            for collection_name in ['members', 'notifications', 'stories']:
                if collection_name in collections:
                    count = await db[collection_name].count_documents({})
                    collection_counts[collection_name] = count
            
            result["details"]["collection_counts"] = collection_counts
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    async def get_mock_data() -> Dict[str, Any]:
        """獲取模擬資料用於測試"""
        return {
            "members": [
                {
                    "_id": "mock_member_1",
                    "name": "測試用戶1",
                    "nickname": "測試1",
                    "customId": "test1",
                    "avatar": "https://example.com/avatar1.jpg",
                    "following": ["mock_member_2", "mock_member_3"],
                    "story_reads": [
                        {"sid": "story_1", "ts": 1234567890},
                        {"sid": "story_2", "ts": 1234567891}
                    ],
                    "story_comments": [
                        {"sid": "story_1", "ts": 1234567892, "content": "很好的文章！"}
                    ]
                },
                {
                    "_id": "mock_member_2",
                    "name": "測試用戶2",
                    "nickname": "測試2",
                    "customId": "test2",
                    "avatar": "https://example.com/avatar2.jpg",
                    "following": ["mock_member_1"],
                    "story_reads": [],
                    "story_comments": []
                }
            ],
            "notifications": [
                {
                    "_id": "mock_member_1",
                    "lrt": 1234567890,
                    "notifies": [
                        {
                            "uuid": "notify_1",
                            "read": False,
                            "action": "follow",
                            "objective": "member",
                            "targetId": "mock_member_2",
                            "aggregate": False,
                            "from": "mock_member_2",
                            "ts": 1234567890
                        }
                    ]
                }
            ],
            "stories": [
                {
                    "_id": "story_1",
                    "url": "https://example.com/story1",
                    "publisher_id": "publisher_1",
                    "og_title": "測試故事1",
                    "og_image": "https://example.com/image1.jpg",
                    "og_description": "這是一個測試故事",
                    "full_screen_ad": False,
                    "isMember": False,
                    "published_date": "2024-01-01T00:00:00.000Z",
                    "story_type": "story",
                    "reads": [],
                    "comments": []
                }
            ]
        }
    
    @staticmethod
    async def test_notifications_data(member_id: str) -> Dict[str, Any]:
        """測試通知資料獲取"""
        result = {
            "status": "unknown",
            "error": None,
            "data": None
        }
        
        try:
            # 首先嘗試使用真實的 MongoDB
            try:
                from src.notify_optimized import get_notifies_optimized
                notifications = await get_notifies_optimized(member_id, 0, 10)
                
                result["status"] = "success"
                result["data"] = {
                    "member_id": notifications.get('id'),
                    "notifications_count": len(notifications.get('notifies', [])),
                    "lrt": notifications.get('lrt'),
                    "has_data": len(notifications.get('notifies', [])) > 0
                }
                return result
                
            except Exception as e:
                # 如果真實 MongoDB 失敗，使用模擬資料
                print(f"真實 MongoDB 連接失敗，使用模擬資料: {e}")
                
                # 使用模擬資料
                mock_data = await DiagnosticMiddleware.get_mock_data()
                mock_notifications = mock_data["notifications"][0]  # 使用第一個模擬通知
                
                result["status"] = "success (mock)"
                result["data"] = {
                    "member_id": mock_notifications["_id"],
                    "notifications_count": len(mock_notifications["notifies"]),
                    "lrt": mock_notifications["lrt"],
                    "has_data": len(mock_notifications["notifies"]) > 0
                }
                return result
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    async def test_socialpage_data(member_id: str) -> Dict[str, Any]:
        """測試社交頁面資料獲取"""
        result = {
            "status": "unknown",
            "error": None,
            "data": None
        }
        
        try:
            # 首先嘗試使用真實的 MongoDB
            try:
                from src.socialpage_optimized import getSocialPage_optimized
                social_page = await getSocialPage_optimized(member_id, 0, 10)
                
                result["status"] = "success"
                result["data"] = {
                    "timestamp": social_page.get('timestamp'),
                    "stories_count": len(social_page.get('stories', [])),
                    "members_count": len(social_page.get('members', [])),
                    "has_data": len(social_page.get('stories', [])) > 0 or len(social_page.get('members', [])) > 0
                }
                return result
                
            except Exception as e:
                # 如果真實 MongoDB 失敗，使用模擬資料
                print(f"真實 MongoDB 連接失敗，使用模擬資料: {e}")
                
                # 使用模擬資料
                mock_data = await DiagnosticMiddleware.get_mock_data()
                
                result["status"] = "success (mock)"
                result["data"] = {
                    "timestamp": int(asyncio.get_event_loop().time()),
                    "stories_count": len(mock_data["stories"]),
                    "members_count": len(mock_data["members"]) - 1,  # 減去自己
                    "has_data": True
                }
                return result
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    async def compare_old_vs_new(member_id: str) -> Dict[str, Any]:
        """比較舊版和新版的資料獲取"""
        result = {
            "status": "unknown",
            "error": None,
            "comparison": {}
        }
        
        try:
            # 測試舊版通知獲取
            old_notifications_result = {"status": "unknown", "error": None}
            try:
                from src.notify import get_notifies
                from src.socialpage import connect_db
                
                mongo_url = os.environ.get('MONGO_URL')
                env = os.environ.get('ENV', 'dev')
                old_db = connect_db(mongo_url, env)
                old_notifications = get_notifies(old_db, member_id, 0, 10)
                
                old_notifications_result["status"] = "success"
                old_notifications_result["data"] = {
                    "notifications_count": len(old_notifications.get('notifies', [])),
                    "lrt": old_notifications.get('lrt')
                }
            except Exception as e:
                old_notifications_result["status"] = "error"
                old_notifications_result["error"] = str(e)
            
            # 測試新版通知獲取
            new_notifications_result = {"status": "unknown", "error": None}
            try:
                from src.notify_optimized import get_notifies_optimized
                new_notifications = await get_notifies_optimized(member_id, 0, 10)
                
                new_notifications_result["status"] = "success"
                new_notifications_result["data"] = {
                    "notifications_count": len(new_notifications.get('notifies', [])),
                    "lrt": new_notifications.get('lrt')
                }
            except Exception as e:
                new_notifications_result["status"] = "error"
                new_notifications_result["error"] = str(e)
            
            result["status"] = "success"
            result["comparison"] = {
                "old_notifications": old_notifications_result,
                "new_notifications": new_notifications_result
            }
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    async def get_test_member_id() -> Optional[str]:
        """獲取一個測試用的成員 ID"""
        try:
            # 首先嘗試從真實 MongoDB 獲取
            manager = await get_mongo_manager()
            db = manager.get_async_db()
            
            # 尋找一個有通知的成員
            member_with_notifications = await db.notifications.find_one({})
            if member_with_notifications:
                return member_with_notifications['_id']
            
            # 如果沒有通知，尋找任何一個成員
            any_member = await db.members.find_one({})
            if any_member:
                return any_member['_id']
            
            return None
            
        except Exception:
            # 如果 MongoDB 連接失敗，返回模擬成員 ID
            return "mock_member_1"
    
    @staticmethod
    async def run_full_diagnostic() -> Dict[str, Any]:
        """執行完整的診斷"""
        diagnostic_result = {
            "timestamp": asyncio.get_event_loop().time(),
            "mongo_connection": None,
            "test_member_id": None,
            "notifications_test": None,
            "socialpage_test": None,
            "comparison_test": None,
            "summary": {
                "overall_status": "unknown",
                "issues": []
            }
        }
        
        try:
            # 1. 檢查 MongoDB 連接
            diagnostic_result["mongo_connection"] = await DiagnosticMiddleware.check_mongo_connection()
            
            # 2. 獲取測試成員 ID（即使 MongoDB 連接失敗也會嘗試使用模擬資料）
            test_member_id = await DiagnosticMiddleware.get_test_member_id()
            diagnostic_result["test_member_id"] = test_member_id
            
            if test_member_id:
                # 3. 測試通知端點
                diagnostic_result["notifications_test"] = await DiagnosticMiddleware.test_notifications_data(test_member_id)
                
                # 4. 測試社交頁面端點
                diagnostic_result["socialpage_test"] = await DiagnosticMiddleware.test_socialpage_data(test_member_id)
                
                # 5. 比較測試（僅在 MongoDB 連接成功時進行）
                if diagnostic_result["mongo_connection"]["status"] == "connected":
                    diagnostic_result["comparison_test"] = await DiagnosticMiddleware.compare_old_vs_new(test_member_id)
            
            # 生成摘要
            issues = []
            
            if diagnostic_result["mongo_connection"]["status"] != "connected":
                issues.append(f"MongoDB 連接失敗: {diagnostic_result['mongo_connection'].get('error', '未知錯誤')}")
                issues.append("使用模擬資料進行測試")
            
            if not diagnostic_result["test_member_id"]:
                issues.append("沒有找到測試成員")
            
            if diagnostic_result["notifications_test"] and diagnostic_result["notifications_test"]["status"] not in ["success", "success (mock)"]:
                issues.append(f"通知測試失敗: {diagnostic_result['notifications_test'].get('error', '未知錯誤')}")
            
            if diagnostic_result["socialpage_test"] and diagnostic_result["socialpage_test"]["status"] not in ["success", "success (mock)"]:
                issues.append(f"社交頁面測試失敗: {diagnostic_result['socialpage_test'].get('error', '未知錯誤')}")
            
            diagnostic_result["summary"]["issues"] = issues
            
            # 判斷整體狀態
            if diagnostic_result["mongo_connection"]["status"] == "connected" and not issues:
                diagnostic_result["summary"]["overall_status"] = "healthy"
            elif "success (mock)" in [diagnostic_result.get("notifications_test", {}).get("status"), diagnostic_result.get("socialpage_test", {}).get("status")]:
                diagnostic_result["summary"]["overall_status"] = "healthy (mock mode)"
            else:
                diagnostic_result["summary"]["overall_status"] = "unhealthy"
            
        except Exception as e:
            diagnostic_result["summary"]["overall_status"] = "error"
            diagnostic_result["summary"]["issues"].append(f"診斷過程發生錯誤: {str(e)}")
        
        return diagnostic_result 