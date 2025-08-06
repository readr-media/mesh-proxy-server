#!/usr/bin/env python3
"""
測試 notify.py 的 get_notifies 函數
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import copy
from src.notify import get_notifies, empty_notifies, empty_mongo_notifies
import src.config as config


class TestGetNotifies(unittest.TestCase):
    """測試 get_notifies 函數的各種情況"""

    def setUp(self):
        """設置測試環境"""
        self.member_id = "test_member_123"
        self.mock_db = Mock()
        self.mock_collection = Mock()
        self.mock_db.notifications = self.mock_collection

    def tearDown(self):
        """清理測試環境"""
        # 清理環境變數
        if 'MESH_GQL_ENDPOINT' in os.environ:
            del os.environ['MESH_GQL_ENDPOINT']

    @patch('src.notify.gql_query')
    def test_get_notifies_without_gql_endpoint(self, mock_gql_query):
        """測試沒有設置 MESH_GQL_ENDPOINT 環境變數的情況"""
        # 確保環境變數未設置
        if 'MESH_GQL_ENDPOINT' in os.environ:
            del os.environ['MESH_GQL_ENDPOINT']
        
        result = get_notifies(self.mock_db, self.member_id)
        
        # 驗證返回空的通知結構
        expected = copy.deepcopy(empty_notifies)
        expected["id"] = self.member_id
        self.assertEqual(result, expected)
        
        # 驗證沒有調用 gql_query
        mock_gql_query.assert_not_called()

    @patch('src.notify.gql_query')
    def test_get_notifies_mongodb_connection_failed(self, mock_gql_query):
        """測試 MongoDB 連接失敗的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        
        # 模擬 MongoDB 連接失敗
        self.mock_db.command.side_effect = Exception("Connection failed")
        
        result = get_notifies(self.mock_db, self.member_id)
        
        # 驗證返回空的通知結構
        expected = copy.deepcopy(empty_notifies)
        expected["id"] = self.member_id
        self.assertEqual(result, expected)
        
        # 驗證沒有調用 gql_query
        mock_gql_query.assert_not_called()

    @patch('src.notify.gql_query')
    def test_get_notifies_no_record_found(self, mock_gql_query):
        """測試沒有找到通知記錄的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        
        # 模擬 MongoDB 連接成功但沒有找到記錄
        self.mock_db.command.return_value = {"ok": 1}
        self.mock_collection.find_one.return_value = None
        
        result = get_notifies(self.mock_db, self.member_id)
        
        # 驗證返回空的通知結構
        expected = copy.deepcopy(empty_notifies)
        expected["id"] = self.member_id
        self.assertEqual(result, expected)
        
        # 驗證插入了空的 MongoDB 記錄
        expected_mongo_record = copy.deepcopy(empty_mongo_notifies)
        expected_mongo_record["_id"] = self.member_id
        self.mock_collection.insert_one.assert_called_once_with(expected_mongo_record)
        
        # 驗證沒有調用 gql_query
        mock_gql_query.assert_not_called()

    @patch('src.notify.gql_query')
    def test_get_notifies_with_payment_notifications(self, mock_gql_query):
        """測試包含支付通知的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        
        # 模擬 MongoDB 記錄
        mock_record = {
            "_id": self.member_id,
            "lrt": 1234567890,
            "notifies": [
                {
                    "uuid": "payment_uuid_1",
                    "action": "notify_transaction",  # 支付通知
                    "from": "member_456",
                    "aggregate": False,
                    "objective": "payment",
                    "targetId": "payment_123",
                    "read": False,
                    "ts": 1234567890
                }
            ]
        }
        
        # 模擬 GQL 查詢結果（空結果，因為支付通知不需要查詢成員信息）
        mock_gql_query.return_value = ({"members": []}, None)
        
        self.mock_db.command.return_value = {"ok": 1}
        self.mock_collection.find_one.return_value = mock_record
        
        result = get_notifies(self.mock_db, self.member_id)
        
        # 驗證結果
        self.assertEqual(result["id"], self.member_id)
        self.assertEqual(result["lrt"], 1234567890)
        self.assertEqual(len(result["notifies"]), 1)
        
        # 驗證支付通知沒有被處理（直接返回原樣）
        payment_notify = result["notifies"][0]
        self.assertEqual(payment_notify["action"], "notify_transaction")
        self.assertEqual(payment_notify["uuid"], "payment_uuid_1")
        
        # 驗證調用了 gql_query（但沒有查詢到成員信息，因為支付通知的 from 字段被跳過了）
        mock_gql_query.assert_called_once()

    @patch('src.notify.gql_query')
    def test_get_notifies_with_single_notification(self, mock_gql_query):
        """測試單個通知的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        
        # 模擬 MongoDB 記錄
        mock_record = {
            "_id": self.member_id,
            "lrt": 1234567890,
            "notifies": [
                {
                    "uuid": "follow_uuid_1",
                    "action": "follow",
                    "from": "member_456",
                    "aggregate": False,
                    "objective": "member",
                    "targetId": "member_789",
                    "read": False,
                    "ts": 1234567890
                }
            ]
        }
        
        # 模擬 GQL 查詢結果
        mock_gql_query.return_value = ({
            "members": [
                {
                    "id": "member_456",
                    "customId": "test456",
                    "name": "測試用戶456",
                    "avatar": "https://example.com/avatar456.jpg"
                }
            ]
        }, None)
        
        self.mock_db.command.return_value = {"ok": 1}
        self.mock_collection.find_one.return_value = mock_record
        
        result = get_notifies(self.mock_db, self.member_id)
        
        # 驗證結果
        self.assertEqual(result["id"], self.member_id)
        self.assertEqual(result["lrt"], 1234567890)
        self.assertEqual(len(result["notifies"]), 1)
        
        # 驗證通知內容
        notify = result["notifies"][0]
        self.assertEqual(notify["uuid"], "follow_uuid_1")
        self.assertEqual(notify["action"], "follow")
        self.assertEqual(notify["aggregate"], False)
        self.assertEqual(notify["notifiers_num"], 1)
        self.assertEqual(len(notify["notifiers"]), 1)
        self.assertEqual(notify["notifiers"][0]["id"], "member_456")
        self.assertEqual(notify["notifiers"][0]["name"], "測試用戶456")

    @patch('src.notify.gql_query')
    def test_get_notifies_with_aggregate_notification(self, mock_gql_query):
        """測試聚合通知的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        
        # 模擬 MongoDB 記錄
        mock_record = {
            "_id": self.member_id,
            "lrt": 1234567890,
            "notifies": [
                {
                    "uuid": "like_uuid_1",
                    "action": "like",
                    "from": ["member_123", "member_456", "member_789"],
                    "aggregate": True,
                    "objective": "story",
                    "targetId": "story_123",
                    "read": False,
                    "ts": 1234567890
                }
            ]
        }
        
        # 模擬 GQL 查詢結果
        mock_gql_query.return_value = ({
            "members": [
                {
                    "id": "member_123",
                    "customId": "test123",
                    "name": "測試用戶123",
                    "avatar": "https://example.com/avatar123.jpg"
                },
                {
                    "id": "member_456",
                    "customId": "test456",
                    "name": "測試用戶456",
                    "avatar": "https://example.com/avatar456.jpg"
                }
            ]
        }, None)
        
        self.mock_db.command.return_value = {"ok": 1}
        self.mock_collection.find_one.return_value = mock_record
        
        result = get_notifies(self.mock_db, self.member_id)
        
        # 驗證結果
        self.assertEqual(result["id"], self.member_id)
        self.assertEqual(result["lrt"], 1234567890)
        self.assertEqual(len(result["notifies"]), 1)
        
        # 驗證聚合通知內容
        notify = result["notifies"][0]
        self.assertEqual(notify["uuid"], "like_uuid_1")
        self.assertEqual(notify["action"], "like")
        self.assertEqual(notify["aggregate"], True)
        self.assertEqual(notify["notifiers_num"], 3)  # 原始數量
        self.assertEqual(len(notify["notifiers"]), 2)  # 限制顯示數量

    @patch('src.notify.gql_query')
    def test_get_notifies_with_missing_member(self, mock_gql_query):
        """測試成員信息缺失的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        
        # 模擬 MongoDB 記錄
        mock_record = {
            "_id": self.member_id,
            "lrt": 1234567890,
            "notifies": [
                {
                    "uuid": "follow_uuid_1",
                    "action": "follow",
                    "from": "member_999",  # 不存在的成員
                    "aggregate": False,
                    "objective": "member",
                    "targetId": "member_789",
                    "read": False,
                    "ts": 1234567890
                }
            ]
        }
        
        # 模擬 GQL 查詢結果（空結果）
        mock_gql_query.return_value = ({"members": []}, None)
        
        self.mock_db.command.return_value = {"ok": 1}
        self.mock_collection.find_one.return_value = mock_record
        
        result = get_notifies(self.mock_db, self.member_id)
        
        # 驗證結果
        self.assertEqual(result["id"], self.member_id)
        self.assertEqual(result["lrt"], 1234567890)
        self.assertEqual(len(result["notifies"]), 1)
        
        # 驗證通知內容（成員信息為空）
        notify = result["notifies"][0]
        self.assertEqual(notify["uuid"], "follow_uuid_1")
        self.assertEqual(notify["action"], "follow")
        self.assertEqual(notify["notifiers_num"], 1)
        self.assertEqual(len(notify["notifiers"]), 0)  # 沒有找到成員信息

    @patch('src.notify.gql_query')
    def test_get_notifies_with_content_field(self, mock_gql_query):
        """測試包含 content 字段的通知"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        
        # 模擬 MongoDB 記錄
        mock_record = {
            "_id": self.member_id,
            "lrt": 1234567890,
            "notifies": [
                {
                    "uuid": "comment_uuid_1",
                    "action": "comment",
                    "from": "member_456",
                    "aggregate": False,
                    "objective": "story",
                    "targetId": "story_123",
                    "read": False,
                    "ts": 1234567890,
                    "content": "這是一個測試評論內容"
                }
            ]
        }
        
        # 模擬 GQL 查詢結果
        mock_gql_query.return_value = ({
            "members": [
                {
                    "id": "member_456",
                    "customId": "test456",
                    "name": "測試用戶456",
                    "avatar": "https://example.com/avatar456.jpg"
                }
            ]
        }, None)
        
        self.mock_db.command.return_value = {"ok": 1}
        self.mock_collection.find_one.return_value = mock_record
        
        result = get_notifies(self.mock_db, self.member_id)
        
        # 驗證結果
        self.assertEqual(result["id"], self.member_id)
        self.assertEqual(len(result["notifies"]), 1)
        
        # 驗證通知內容包含 content 字段
        notify = result["notifies"][0]
        self.assertEqual(notify["uuid"], "comment_uuid_1")
        self.assertEqual(notify["action"], "comment")
        self.assertEqual(notify["content"], "這是一個測試評論內容")

    @patch('src.notify.gql_query')
    def test_get_notifies_with_pagination(self, mock_gql_query):
        """測試分頁功能"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        
        # 模擬 MongoDB 記錄（多個通知）
        mock_record = {
            "_id": self.member_id,
            "lrt": 1234567890,
            "notifies": [
                {
                    "uuid": "notify_1",
                    "action": "follow",
                    "from": "member_1",
                    "aggregate": False,
                    "objective": "member",
                    "targetId": "member_2",
                    "read": False,
                    "ts": 1234567890
                },
                {
                    "uuid": "notify_2",
                    "action": "like",
                    "from": "member_2",
                    "aggregate": False,
                    "objective": "story",
                    "targetId": "story_1",
                    "read": False,
                    "ts": 1234567891
                },
                {
                    "uuid": "notify_3",
                    "action": "comment",
                    "from": "member_3",
                    "aggregate": False,
                    "objective": "story",
                    "targetId": "story_1",
                    "read": False,
                    "ts": 1234567892
                }
            ]
        }
        
        # 模擬 GQL 查詢結果
        mock_gql_query.return_value = ({
            "members": [
                {
                    "id": "member_1",
                    "customId": "test1",
                    "name": "測試用戶1",
                    "avatar": "https://example.com/avatar1.jpg"
                },
                {
                    "id": "member_2",
                    "customId": "test2",
                    "name": "測試用戶2",
                    "avatar": "https://example.com/avatar2.jpg"
                },
                {
                    "id": "member_3",
                    "customId": "test3",
                    "name": "測試用戶3",
                    "avatar": "https://example.com/avatar3.jpg"
                }
            ]
        }, None)
        
        self.mock_db.command.return_value = {"ok": 1}
        self.mock_collection.find_one.return_value = mock_record
        
        # 測試分頁：index=1, take=2
        result = get_notifies(self.mock_db, self.member_id, index=1, take=2)
        
        # 驗證結果
        self.assertEqual(result["id"], self.member_id)
        self.assertEqual(result["lrt"], 1234567890)
        self.assertEqual(len(result["notifies"]), 2)  # 只返回 2 個通知
        
        # 驗證返回的是第二和第三個通知
        self.assertEqual(result["notifies"][0]["uuid"], "notify_2")
        self.assertEqual(result["notifies"][1]["uuid"], "notify_3")

    @patch('src.notify.gql_query')
    def test_get_notifies_gql_query_error(self, mock_gql_query):
        """測試 GQL 查詢錯誤的情況"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        
        # 模擬 MongoDB 記錄
        mock_record = {
            "_id": self.member_id,
            "lrt": 1234567890,
            "notifies": [
                {
                    "uuid": "follow_uuid_1",
                    "action": "follow",
                    "from": "member_456",
                    "aggregate": False,
                    "objective": "member",
                    "targetId": "member_789",
                    "read": False,
                    "ts": 1234567890
                }
            ]
        }
        
        # 模擬 GQL 查詢錯誤
        mock_gql_query.return_value = (None, "GQL query failed")
        
        self.mock_db.command.return_value = {"ok": 1}
        self.mock_collection.find_one.return_value = mock_record
        
        result = get_notifies(self.mock_db, self.member_id)
        
        # 驗證結果（應該返回空的通知列表）
        expected = copy.deepcopy(empty_notifies)
        expected["id"] = self.member_id
        self.assertEqual(result, expected)

    def test_get_notifies_exception_handling(self):
        """測試異常處理"""
        # 設置環境變數
        os.environ['MESH_GQL_ENDPOINT'] = 'http://test-endpoint.com'
        
        # 模擬 MongoDB 記錄（包含無效數據）
        mock_record = {
            "_id": self.member_id,
            "lrt": 1234567890,
            "notifies": [
                {
                    "uuid": "invalid_uuid",
                    "action": "follow",
                    "from": None,  # 無效的 from 字段
                    "aggregate": False,
                    "objective": "member",
                    "targetId": "member_789",
                    "read": False,
                    "ts": 1234567890
                }
            ]
        }
        
        self.mock_db.command.return_value = {"ok": 1}
        self.mock_collection.find_one.return_value = mock_record
        
        # 應該不會拋出異常，而是返回空結果
        result = get_notifies(self.mock_db, self.member_id)
        
        # 驗證結果
        expected = copy.deepcopy(empty_notifies)
        expected["id"] = self.member_id
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main() 