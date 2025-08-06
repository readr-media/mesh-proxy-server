#!/usr/bin/env python3
"""
測試 socialpage.py 的 getSocialPage 函數
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import os
import json
import asyncio
from datetime import datetime
from src.socialpage import getSocialPage, connect_db
import src.config as config


class TestGetSocialPage(unittest.TestCase):
    """測試 getSocialPage 函數的各種情況"""

    def setUp(self):
        """設置測試環境"""
        self.member_id = "test_member_123"
        self.mongo_url = "mongodb://test-mongo-url"
        self.mock_db = Mock()
        self.mock_collection_members = Mock()
        self.mock_collection_stories = Mock()
        self.mock_db.members = self.mock_collection_members
        self.mock_db.stories = self.mock_collection_stories

    def tearDown(self):
        """清理測試環境"""
        # 清理環境變數
        if 'MESH_GQL_ENDPOINT' in os.environ:
            del os.environ['MESH_GQL_ENDPOINT']
        if 'ENV' in os.environ:
            del os.environ['ENV']

    @patch('src.socialpage.connect_db')
    @patch('src.socialpage.gql_query')
    @patch('src.socialpage.get_cache')
    @patch('src.socialpage.set_cache')
    @patch('src.socialpage.FastAPICache')
    async def test_get_social_page_with_cache(self, mock_fastapi_cache, mock_set_cache, mock_get_cache, mock_gql_query, mock_connect_db):
        """測試有緩存數據的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        os.environ['ENV'] = 'dev'
        
        # 模擬緩存數據
        cached_data = {
            "timestamp": 1234567890,
            "stories": [
                {
                    "id": "story_1",
                    "url": "https://example.com/story1",
                    "publisher": {"id": "pub_1", "title": "測試出版社", "customId": "test_pub"},
                    "og_title": "測試故事標題",
                    "og_image": "https://example.com/image1.jpg",
                    "og_description": "測試故事描述",
                    "full_screen_ad": False,
                    "isMember": True,
                    "published_date": "2023-01-01",
                    "story_type": "story",
                    "readCount": 10,
                    "commentCount": 5,
                    "following_actions": [
                        {
                            "kind": "read",
                            "member": {"id": "member_1", "name": "測試用戶"},
                            "createdAt": "2023-01-01T00:00:00.000Z"
                        }
                    ]
                }
            ],
            "members": [
                {
                    "id": "member_2",
                    "followerCount": 100,
                    "name": "推薦用戶",
                    "nickname": "推薦",
                    "customId": "recommend_user",
                    "avatar": "https://example.com/avatar2.jpg",
                    "from": {"id": "member_1", "name": "推薦來源", "nickname": "來源"}
                }
            ]
        }
        
        # 模擬緩存返回
        mock_get_cache.return_value = (True, json.dumps(cached_data))
        mock_fastapi_cache.get_prefix.return_value = "test_prefix"
        
        # 執行測試
        result = await getSocialPage(self.mongo_url, self.member_id)
        
        # 驗證結果
        self.assertEqual(result["timestamp"], 1234567890)
        self.assertEqual(len(result["stories"]), 1)
        self.assertEqual(len(result["members"]), 1)
        self.assertEqual(result["stories"][0]["id"], "story_1")
        self.assertEqual(result["members"][0]["id"], "member_2")
        
        # 驗證沒有調用數據庫查詢
        mock_connect_db.assert_not_called()
        mock_gql_query.assert_not_called()

    @patch('src.socialpage.connect_db')
    @patch('src.socialpage.gql_query')
    @patch('src.socialpage.get_cache')
    @patch('src.socialpage.set_cache')
    @patch('src.socialpage.FastAPICache')
    async def test_get_social_page_no_cache(self, mock_fastapi_cache, mock_set_cache, mock_get_cache, mock_gql_query, mock_connect_db):
        """測試沒有緩存數據的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        os.environ['ENV'] = 'dev'
        
        # 模擬沒有緩存數據
        mock_get_cache.return_value = (False, None)
        mock_fastapi_cache.get_prefix.return_value = "test_prefix"
        
        # 模擬 GQL 查詢結果
        mock_gql_query.return_value = ({
            "publishers": [
                {
                    "id": "pub_1",
                    "title": "測試出版社",
                    "customId": "test_pub"
                }
            ]
        }, None)
        
        # 模擬數據庫連接
        mock_connect_db.return_value = self.mock_db
        
        # 模擬成員數據
        member_info = {
            "_id": self.member_id,
            "following": ["member_1", "member_2"]
        }
        
        followings_info = [
            {
                "_id": "member_1",
                "name": "用戶1",
                "nickname": "用戶1暱稱",
                "customId": "user1",
                "avatar": "https://example.com/avatar1.jpg",
                "is_active": True,
                "following": ["member_3", "member_4"],
                "story_reads": [
                    {
                        "sid": "story_1",
                        "ts": 1234567890
                    }
                ],
                "story_comments": [
                    {
                        "sid": "story_2",
                        "ts": 1234567891,
                        "content": "測試評論"
                    }
                ]
            },
            {
                "_id": "member_2",
                "name": "用戶2",
                "nickname": "用戶2暱稱",
                "customId": "user2",
                "avatar": "https://example.com/avatar2.jpg",
                "is_active": True,
                "following": ["member_3", "member_5"],
                "story_reads": [],
                "story_comments": []
            }
        ]
        
        # 模擬推薦成員數據
        recommended_members = [
            {
                "_id": "member_3",
                "name": "推薦用戶3",
                "nickname": "推薦3",
                "customId": "recommend3",
                "avatar": "https://example.com/avatar3.jpg",
                "follower": ["follower1", "follower2"]
            }
        ]
        
        # 模擬故事數據
        stories_data = [
            {
                "_id": "story_1",
                "url": "https://example.com/story1",
                "publisher_id": "pub_1",
                "og_title": "故事1標題",
                "og_image": "https://example.com/image1.jpg",
                "og_description": "故事1描述",
                "full_screen_ad": False,
                "isMember": True,
                "published_date": "2023-01-01",
                "story_type": "story",
                "reads": ["read1", "read2"],
                "comments": ["comment1"]
            },
            {
                "_id": "story_2",
                "url": "https://example.com/story2",
                "publisher_id": "pub_1",
                "og_title": "故事2標題",
                "og_image": "https://example.com/image2.jpg",
                "og_description": "故事2描述",
                "full_screen_ad": True,
                "isMember": False,
                "published_date": "2023-01-02",
                "story_type": "story",
                "reads": ["read3"],
                "comments": ["comment2", "comment3"]
            }
        ]
        
        # 設置數據庫查詢結果
        self.mock_collection_members.find_one.return_value = member_info
        self.mock_collection_members.find.return_value = followings_info
        self.mock_collection_members.find.return_value = recommended_members
        self.mock_collection_stories.find.return_value = stories_data
        
        # 執行測試
        result = await getSocialPage(self.mongo_url, self.member_id)
        
        # 驗證結果
        self.assertIn("timestamp", result)
        self.assertIn("stories", result)
        self.assertIn("members", result)
        
        # 驗證調用了緩存設置
        mock_set_cache.assert_called_once()
        
        # 驗證調用了數據庫查詢
        mock_connect_db.assert_called_once_with(self.mongo_url, 'dev')
        mock_gql_query.assert_called_once()

    @patch('src.socialpage.connect_db')
    @patch('src.socialpage.gql_query')
    @patch('src.socialpage.get_cache')
    @patch('src.socialpage.set_cache')
    @patch('src.socialpage.FastAPICache')
    async def test_get_social_page_with_pagination(self, mock_fastapi_cache, mock_set_cache, mock_get_cache, mock_gql_query, mock_connect_db):
        """測試分頁功能"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        os.environ['ENV'] = 'dev'
        
        # 模擬緩存數據
        cached_data = {
            "timestamp": 1234567890,
            "stories": [
                {"id": "story_1", "title": "故事1"},
                {"id": "story_2", "title": "故事2"},
                {"id": "story_3", "title": "故事3"},
                {"id": "story_4", "title": "故事4"},
                {"id": "story_5", "title": "故事5"}
            ],
            "members": []
        }
        
        mock_get_cache.return_value = (True, json.dumps(cached_data))
        mock_fastapi_cache.get_prefix.return_value = "test_prefix"
        
        # 測試分頁：index=1, take=2
        result = await getSocialPage(self.mongo_url, self.member_id, index=1, take=2)
        
        # 驗證結果
        self.assertEqual(len(result["stories"]), 2)
        self.assertEqual(result["stories"][0]["id"], "story_2")
        self.assertEqual(result["stories"][1]["id"], "story_3")

    @patch('src.socialpage.connect_db')
    @patch('src.socialpage.gql_query')
    @patch('src.socialpage.get_cache')
    @patch('src.socialpage.set_cache')
    @patch('src.socialpage.FastAPICache')
    async def test_get_social_page_inactive_members(self, mock_fastapi_cache, mock_set_cache, mock_get_cache, mock_gql_query, mock_connect_db):
        """測試非活躍成員的處理"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        os.environ['ENV'] = 'dev'
        
        # 模擬沒有緩存數據
        mock_get_cache.return_value = (False, None)
        mock_fastapi_cache.get_prefix.return_value = "test_prefix"
        
        # 模擬 GQL 查詢結果
        mock_gql_query.return_value = ({"publishers": []}, None)
        
        # 模擬數據庫連接
        mock_connect_db.return_value = self.mock_db
        
        # 模擬成員數據（包含非活躍成員）
        member_info = {
            "_id": self.member_id,
            "following": ["member_1", "member_2"]
        }
        
        followings_info = [
            {
                "_id": "member_1",
                "name": "活躍用戶",
                "nickname": "活躍",
                "customId": "active_user",
                "avatar": "https://example.com/avatar1.jpg",
                "is_active": True,
                "following": ["member_3"],
                "story_reads": [],
                "story_comments": []
            },
            {
                "_id": "member_2",
                "name": "非活躍用戶",
                "nickname": "非活躍",
                "customId": "inactive_user",
                "avatar": "https://example.com/avatar2.jpg",
                "is_active": False,  # 非活躍
                "following": ["member_4"],
                "story_reads": [],
                "story_comments": []
            }
        ]
        
        # 設置數據庫查詢結果
        self.mock_collection_members.find_one.return_value = member_info
        self.mock_collection_members.find.return_value = followings_info
        
        # 執行測試
        result = await getSocialPage(self.mongo_url, self.member_id)
        
        # 驗證結果
        self.assertIn("timestamp", result)
        self.assertIn("stories", result)
        self.assertIn("members", result)
        
        # 驗證非活躍成員被正確處理（不會出現在推薦中）

    @patch('src.socialpage.connect_db')
    @patch('src.socialpage.gql_query')
    @patch('src.socialpage.get_cache')
    @patch('src.socialpage.set_cache')
    @patch('src.socialpage.FastAPICache')
    async def test_get_social_page_story_without_publisher(self, mock_fastapi_cache, mock_set_cache, mock_get_cache, mock_gql_query, mock_connect_db):
        """測試沒有出版社的故事處理"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        os.environ['ENV'] = 'dev'
        
        # 模擬沒有緩存數據
        mock_get_cache.return_value = (False, None)
        mock_fastapi_cache.get_prefix.return_value = "test_prefix"
        
        # 模擬 GQL 查詢結果
        mock_gql_query.return_value = ({"publishers": []}, None)
        
        # 模擬數據庫連接
        mock_connect_db.return_value = self.mock_db
        
        # 模擬成員數據
        member_info = {
            "_id": self.member_id,
            "following": ["member_1"]
        }
        
        followings_info = [
            {
                "_id": "member_1",
                "name": "用戶1",
                "nickname": "用戶1暱稱",
                "customId": "user1",
                "avatar": "https://example.com/avatar1.jpg",
                "is_active": True,
                "following": [],
                "story_reads": [
                    {
                        "sid": "story_1",
                        "ts": 1234567890
                    }
                ],
                "story_comments": []
            }
        ]
        
        # 模擬故事數據（沒有出版社）
        stories_data = [
            {
                "_id": "story_1",
                "url": "https://example.com/story1",
                "publisher_id": None,  # 沒有出版社
                "og_title": "故事標題",
                "og_image": "https://example.com/image1.jpg",
                "og_description": "故事描述",
                "full_screen_ad": False,
                "isMember": True,
                "published_date": "2023-01-01",
                "story_type": "story",
                "reads": ["read1"],
                "comments": []
            }
        ]
        
        # 設置數據庫查詢結果
        self.mock_collection_members.find_one.return_value = member_info
        self.mock_collection_members.find.return_value = followings_info
        self.mock_collection_stories.find.return_value = stories_data
        
        # 執行測試
        result = await getSocialPage(self.mongo_url, self.member_id)
        
        # 驗證結果
        self.assertIn("timestamp", result)
        self.assertIn("stories", result)
        self.assertIn("members", result)
        
        # 驗證沒有出版社的故事不會出現在結果中
        story_ids = [story["id"] for story in result["stories"]]
        self.assertNotIn("story_1", story_ids)

    @patch('src.socialpage.connect_db')
    @patch('src.socialpage.gql_query')
    @patch('src.socialpage.get_cache')
    @patch('src.socialpage.set_cache')
    @patch('src.socialpage.FastAPICache')
    async def test_get_social_page_gql_error(self, mock_fastapi_cache, mock_set_cache, mock_get_cache, mock_gql_query, mock_connect_db):
        """測試 GQL 查詢錯誤的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        os.environ['ENV'] = 'dev'
        
        # 模擬沒有緩存數據
        mock_get_cache.return_value = (False, None)
        mock_fastapi_cache.get_prefix.return_value = "test_prefix"
        
        # 模擬 GQL 查詢錯誤
        mock_gql_query.return_value = (None, "GQL query failed")
        
        # 執行測試
        result = await getSocialPage(self.mongo_url, self.member_id)
        
        # 驗證結果（應該返回空的社交頁面）
        self.assertIn("timestamp", result)
        self.assertIn("stories", result)
        self.assertIn("members", result)
        self.assertEqual(len(result["stories"]), 0)
        self.assertEqual(len(result["members"]), 0)

    @patch('src.socialpage.connect_db')
    @patch('src.socialpage.gql_query')
    @patch('src.socialpage.get_cache')
    @patch('src.socialpage.set_cache')
    @patch('src.socialpage.FastAPICache')
    async def test_get_social_page_member_not_found(self, mock_fastapi_cache, mock_set_cache, mock_get_cache, mock_gql_query, mock_connect_db):
        """測試成員不存在的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        os.environ['ENV'] = 'dev'
        
        # 模擬沒有緩存數據
        mock_get_cache.return_value = (False, None)
        mock_fastapi_cache.get_prefix.return_value = "test_prefix"
        
        # 模擬 GQL 查詢結果
        mock_gql_query.return_value = ({"publishers": []}, None)
        
        # 模擬數據庫連接
        mock_connect_db.return_value = self.mock_db
        
        # 模擬成員不存在
        self.mock_collection_members.find_one.return_value = None
        
        # 執行測試
        result = await getSocialPage(self.mongo_url, self.member_id)
        
        # 驗證結果（應該返回空的社交頁面）
        self.assertIn("timestamp", result)
        self.assertIn("stories", result)
        self.assertIn("members", result)
        self.assertEqual(len(result["stories"]), 0)
        self.assertEqual(len(result["members"]), 0)

    def test_connect_db_dev_environment(self):
        """測試開發環境的數據庫連接"""
        with patch('src.socialpage.pymongo.MongoClient') as mock_client:
            mock_client.return_value.dev = self.mock_db
            
            result = connect_db("mongodb://test-url", "dev")
            
            self.assertEqual(result, self.mock_db)
            mock_client.assert_called_once_with("mongodb://test-url")

    def test_connect_db_prod_environment(self):
        """測試生產環境的數據庫連接"""
        with patch('src.socialpage.pymongo.MongoClient') as mock_client:
            mock_client.return_value.prod = self.mock_db
            
            result = connect_db("mongodb://test-url", "prod")
            
            self.assertEqual(result, self.mock_db)
            mock_client.assert_called_once_with("mongodb://test-url")

    def test_connect_db_staging_environment(self):
        """測試測試環境的數據庫連接"""
        with patch('src.socialpage.pymongo.MongoClient') as mock_client:
            mock_client.return_value.staging = self.mock_db
            
            result = connect_db("mongodb://test-url", "staging")
            
            self.assertEqual(result, self.mock_db)
            mock_client.assert_called_once_with("mongodb://test-url")

    @patch('src.socialpage.connect_db')
    @patch('src.socialpage.gql_query')
    @patch('src.socialpage.get_cache')
    @patch('src.socialpage.set_cache')
    @patch('src.socialpage.FastAPICache')
    async def test_get_social_page_empty_following_list(self, mock_fastapi_cache, mock_set_cache, mock_get_cache, mock_gql_query, mock_connect_db):
        """測試用戶沒有關注任何人的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        os.environ['ENV'] = 'dev'
        
        # 模擬沒有緩存數據
        mock_get_cache.return_value = (False, None)
        mock_fastapi_cache.get_prefix.return_value = "test_prefix"
        
        # 模擬 GQL 查詢結果
        mock_gql_query.return_value = ({"publishers": []}, None)
        
        # 模擬數據庫連接
        mock_connect_db.return_value = self.mock_db
        
        # 模擬成員沒有關注任何人
        member_info = {
            "_id": self.member_id,
            "following": []
        }
        self.mock_collection_members.find_one.return_value = member_info
        
        # 執行測試
        result = await getSocialPage(self.mongo_url, self.member_id)
        
        # 驗證結果
        self.assertIn("timestamp", result)
        self.assertIn("stories", result)
        self.assertIn("members", result)
        self.assertEqual(len(result["stories"]), 0)
        self.assertEqual(len(result["members"]), 0)

    @patch('src.socialpage.connect_db')
    @patch('src.socialpage.gql_query')
    @patch('src.socialpage.get_cache')
    @patch('src.socialpage.set_cache')
    @patch('src.socialpage.FastAPICache')
    async def test_get_social_page_large_pagination(self, mock_fastapi_cache, mock_set_cache, mock_get_cache, mock_gql_query, mock_connect_db):
        """測試大分頁參數的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        os.environ['ENV'] = 'dev'
        
        # 模擬緩存數據
        cached_data = {
            "timestamp": 1234567890,
            "stories": [
                {"id": f"story_{i}", "url": f"https://example.com/story{i}"} for i in range(10)
            ],
            "members": []
        }
        mock_get_cache.return_value = (True, json.dumps(cached_data))
        mock_fastapi_cache.get_prefix.return_value = "test_prefix"
        
        # 執行測試 - 使用大的分頁參數
        result = await getSocialPage(self.mongo_url, self.member_id, index=100, take=50)
        
        # 驗證結果 - 應該返回空列表
        self.assertEqual(len(result["stories"]), 0)

    @patch('src.socialpage.connect_db')
    @patch('src.socialpage.gql_query')
    @patch('src.socialpage.get_cache')
    @patch('src.socialpage.set_cache')
    @patch('src.socialpage.FastAPICache')
    async def test_get_social_page_negative_pagination(self, mock_fastapi_cache, mock_set_cache, mock_get_cache, mock_gql_query, mock_connect_db):
        """測試負數分頁參數的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        os.environ['ENV'] = 'dev'
        
        # 模擬緩存數據
        cached_data = {
            "timestamp": 1234567890,
            "stories": [
                {"id": f"story_{i}", "url": f"https://example.com/story{i}"} for i in range(5)
            ],
            "members": []
        }
        mock_get_cache.return_value = (True, json.dumps(cached_data))
        mock_fastapi_cache.get_prefix.return_value = "test_prefix"
        
        # 執行測試 - 使用負數分頁參數
        result = await getSocialPage(self.mongo_url, self.member_id, index=-1, take=3)
        
        # 驗證結果 - 應該返回原始數據（因為負數索引不會觸發分頁）
        self.assertEqual(len(result["stories"]), 5)

    @patch('src.socialpage.connect_db')
    @patch('src.socialpage.gql_query')
    @patch('src.socialpage.get_cache')
    @patch('src.socialpage.set_cache')
    @patch('src.socialpage.FastAPICache')
    async def test_get_social_page_cache_set_error(self, mock_fastapi_cache, mock_set_cache, mock_get_cache, mock_gql_query, mock_connect_db):
        """測試緩存設置失敗的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        os.environ['ENV'] = 'dev'
        
        # 模擬沒有緩存數據
        mock_get_cache.return_value = (False, None)
        mock_fastapi_cache.get_prefix.return_value = "test_prefix"
        
        # 模擬 GQL 查詢結果
        mock_gql_query.return_value = ({"publishers": []}, None)
        
        # 模擬數據庫連接
        mock_connect_db.return_value = self.mock_db
        
        # 模擬成員數據
        member_info = {
            "_id": self.member_id,
            "following": []
        }
        self.mock_collection_members.find_one.return_value = member_info
        
        # 模擬緩存設置失敗
        mock_set_cache.side_effect = Exception("Cache set failed")
        
        # 執行測試
        result = await getSocialPage(self.mongo_url, self.member_id)
        
        # 驗證結果 - 即使緩存設置失敗，也應該返回正確的數據
        self.assertIn("timestamp", result)
        self.assertIn("stories", result)
        self.assertIn("members", result)


# 運行異步測試的輔助函數
def async_test(coro):
    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))
    return wrapper


# 將異步測試方法轉換為同步測試
for attr_name in dir(TestGetSocialPage):
    attr = getattr(TestGetSocialPage, attr_name)
    if attr_name.startswith('test_') and asyncio.iscoroutinefunction(attr):
        setattr(TestGetSocialPage, attr_name, async_test(attr))


if __name__ == '__main__':
    unittest.main() 