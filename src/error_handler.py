import traceback
import sys
from typing import Any, Dict, Optional

class ErrorHandler:
    """
    統一的錯誤處理器
    """
    
    @staticmethod
    def handle_gql_error(result: Any, error: Optional[str], operation: str) -> Dict[str, Any]:
        """
        處理 GQL 查詢錯誤
        """
        if error:
            print(f"GQL {operation} error: {error}")
            return {"status": "error", "error": error, "data": None}
        
        if not result:
            print(f"GQL {operation} returned None")
            return {"status": "error", "error": "Query returned None", "data": None}
        
        if not isinstance(result, dict):
            print(f"GQL {operation} returned invalid type: {type(result)}")
            return {"status": "error", "error": f"Invalid response type: {type(result)}", "data": None}
        
        return {"status": "success", "error": None, "data": result}
    
    @staticmethod
    def handle_mongo_error(operation: str, error: Exception) -> Dict[str, Any]:
        """
        處理 MongoDB 操作錯誤
        """
        error_msg = f"MongoDB {operation} error: {str(error)}"
        print(error_msg)
        print(f"Error type: {type(error)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            "status": "error",
            "error": error_msg,
            "operation": operation,
            "error_type": type(error).__name__
        }
    
    @staticmethod
    def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        安全地從字典中獲取值
        """
        try:
            return data.get(key, default)
        except Exception as e:
            print(f"Error accessing key '{key}' from data: {e}")
            return default
    
    @staticmethod
    def safe_list_operation(data: Any, operation: str) -> Any:
        """
        安全地對列表進行操作
        """
        try:
            if not isinstance(data, list):
                print(f"Expected list for {operation}, got {type(data)}")
                return []
            return data
        except Exception as e:
            print(f"Error in list operation '{operation}': {e}")
            return []
    
    @staticmethod
    def log_operation(operation: str, details: Dict[str, Any] = None):
        """
        記錄操作信息
        """
        log_msg = f"Operation: {operation}"
        if details:
            log_msg += f" | Details: {details}"
        print(log_msg)
    
    @staticmethod
    def create_empty_response(response_type: str) -> Dict[str, Any]:
        """
        創建空的回應
        """
        if response_type == "notifications":
            return {
                "id": None,
                "lrt": 0,
                "notifies": []
            }
        elif response_type == "socialpage":
            return {
                "timestamp": 0,
                "stories": [],
                "members": []
            }
        else:
            return {} 