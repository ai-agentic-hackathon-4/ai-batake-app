"""Tests for diary service functions in diary_service.py"""
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import pytest

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCalculateStatistics:
    """Tests for calculate_statistics function"""
    
    def test_calculate_statistics_with_data(self):
        """Test statistics calculation with valid data"""
        from diary_service import calculate_statistics
        
        sensor_data = [
            {"temperature": 20.0, "humidity": 50.0, "soil_moisture": 30.0},
            {"temperature": 25.0, "humidity": 60.0, "soil_moisture": 35.0},
            {"temperature": 22.0, "humidity": 55.0, "soil_moisture": 32.0},
        ]
        
        result = calculate_statistics(sensor_data)
        
        assert result["temperature"]["min"] == 20.0
        assert result["temperature"]["max"] == 25.0
        assert result["temperature"]["avg"] == 22.3  # (20 + 25 + 22) / 3 = 22.33
        
        assert result["humidity"]["min"] == 50.0
        assert result["humidity"]["max"] == 60.0
        assert result["humidity"]["avg"] == 55.0
        
        assert result["soil_moisture"]["min"] == 30.0
        assert result["soil_moisture"]["max"] == 35.0
    
    def test_calculate_statistics_empty_data(self):
        """Test statistics calculation with empty data"""
        from diary_service import calculate_statistics
        
        result = calculate_statistics([])
        
        assert result["temperature"]["min"] == 0
        assert result["temperature"]["max"] == 0
        assert result["temperature"]["avg"] == 0
        assert result["humidity"]["min"] == 0
        assert result["soil_moisture"]["min"] == 0
    
    def test_calculate_statistics_partial_data(self):
        """Test statistics calculation with partial data (some None values)"""
        from diary_service import calculate_statistics
        
        sensor_data = [
            {"temperature": 20.0, "humidity": None, "soil_moisture": 30.0},
            {"temperature": 25.0, "humidity": 60.0, "soil_moisture": None},
        ]
        
        result = calculate_statistics(sensor_data)
        
        assert result["temperature"]["min"] == 20.0
        assert result["temperature"]["max"] == 25.0
        assert result["humidity"]["min"] == 60.0
        assert result["humidity"]["max"] == 60.0


class TestExtractKeyEvents:
    """Tests for extract_key_events function"""
    
    def test_extract_key_events_with_operations(self):
        """Test event extraction with operation logs"""
        from diary_service import extract_key_events
        
        agent_logs = [
            {
                "timestamp": "2025-01-01T10:00:00",
                "data": {
                    "operation": {
                        "pump": {"action": "ON"}
                    }
                }
            },
            {
                "timestamp": "2025-01-01T12:00:00",
                "data": {
                    "operation": {
                        "fan": {"action": "OFF"}
                    }
                }
            }
        ]
        
        events = extract_key_events(agent_logs)
        
        assert len(events) == 2
        assert events[0]["type"] == "action"
        assert events[0]["device"] == "pump"
        assert events[0]["action"] == "ON"
    
    def test_extract_key_events_with_alerts(self):
        """Test event extraction with alert logs"""
        from diary_service import extract_key_events
        
        agent_logs = [
            {
                "timestamp": "2025-01-01T10:00:00",
                "data": {
                    "comment": "異常検知：温度が高すぎます"
                }
            }
        ]
        
        events = extract_key_events(agent_logs)
        
        assert len(events) == 1
        assert events[0]["type"] == "alert"
        assert "異常検知" in events[0]["action"]
    
    def test_extract_key_events_max_limit(self):
        """Test event extraction respects max limit"""
        from diary_service import extract_key_events
        
        # Create 15 events
        agent_logs = [
            {
                "timestamp": f"2025-01-01T{i:02d}:00:00",
                "data": {"comment": f"Event {i}"}
            }
            for i in range(15)
        ]
        
        events = extract_key_events(agent_logs, max_events=5)
        
        assert len(events) == 5
    
    def test_extract_key_events_empty_logs(self):
        """Test event extraction with empty logs"""
        from diary_service import extract_key_events
        
        events = extract_key_events([])
        
        assert events == []


class TestParseDiaryResponse:
    """Tests for parse_diary_response function"""
    
    def test_parse_diary_response_valid_json(self):
        """Test parsing valid JSON response"""
        from diary_service import parse_diary_response
        
        text = '''```json
{
    "summary": "Today was a good day for plants",
    "observations": "Plants are growing well",
    "recommendations": "Continue watering"
}
```'''
        
        result = parse_diary_response(text)
        
        assert result["summary"] == "Today was a good day for plants"
        assert result["observations"] == "Plants are growing well"
        assert result["recommendations"] == "Continue watering"
    
    def test_parse_diary_response_plain_json(self):
        """Test parsing plain JSON without markdown"""
        from diary_service import parse_diary_response
        
        text = '{"summary": "Test summary", "observations": "Test obs", "recommendations": "Test rec"}'
        
        result = parse_diary_response(text)
        
        assert result["summary"] == "Test summary"
    
    def test_parse_diary_response_invalid_json(self):
        """Test parsing invalid JSON (fallback behavior)"""
        from diary_service import parse_diary_response
        
        text = "This is not JSON at all"
        
        result = parse_diary_response(text)
        
        # Should use fallback values
        assert "This is not JSON" in result["summary"]
        assert result["observations"] == "データを分析中です。"


class TestBuildDiaryPrompt:
    """Tests for build_diary_prompt function"""
    
    def test_build_diary_prompt_basic(self):
        """Test building a basic prompt"""
        from diary_service import build_diary_prompt
        
        statistics = {
            "temperature": {"min": 20, "max": 30, "avg": 25},
            "humidity": {"min": 50, "max": 70, "avg": 60},
            "soil_moisture": {"min": 30, "max": 40, "avg": 35}
        }
        
        events = [
            {"time": "10:00", "device": "pump", "action": "ON"}
        ]
        
        vegetable_info = {"name": "トマト"}
        
        prompt = build_diary_prompt("2025-01-01", statistics, events, vegetable_info)
        
        assert "2025-01-01" in prompt
        assert "トマト" in prompt
        assert "20" in prompt  # min temp
        assert "30" in prompt  # max temp
        assert "pump" in prompt
    
    def test_build_diary_prompt_no_vegetable(self):
        """Test building prompt without vegetable info"""
        from diary_service import build_diary_prompt
        
        statistics = {
            "temperature": {"min": 0, "max": 0, "avg": 0},
            "humidity": {"min": 0, "max": 0, "avg": 0},
            "soil_moisture": {"min": 0, "max": 0, "avg": 0}
        }
        
        prompt = build_diary_prompt("2025-01-01", statistics, [], None)
        
        assert "野菜" in prompt  # Fallback name


class TestDiaryServiceDatabase:
    """Tests for diary service database functions"""
    
    @patch('diary_service.db')
    def test_get_all_diaries_success(self, mock_db):
        """Test successful diary list retrieval"""
        from diary_service import get_all_diaries
        
        mock_doc1 = Mock()
        mock_doc1.to_dict.return_value = {
            "date": "2025-01-01",
            "ai_summary": "Test summary",
            "generation_status": "completed"
        }
        mock_doc1.id = "2025-01-01"
        
        mock_query = Mock()
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = [mock_doc1]
        
        mock_collection = Mock()
        mock_collection.where.return_value = mock_query
        
        mock_db.collection.return_value = mock_collection
        
        result = get_all_diaries(limit=10)
        
        assert len(result) == 1
        assert result[0]["date"] == "2025-01-01"
    
    @patch('diary_service.db', None)
    def test_get_all_diaries_no_db(self):
        """Test diary list when db is None"""
        from diary_service import get_all_diaries
        
        result = get_all_diaries()
        
        assert result == []
    
    @patch('diary_service.db')
    def test_get_diary_by_date_success(self, mock_db):
        """Test successful diary retrieval by date"""
        from diary_service import get_diary_by_date
        
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "date": "2025-01-01",
            "ai_summary": "Test summary"
        }
        mock_doc.id = "2025-01-01"
        
        mock_collection = Mock()
        mock_collection.document.return_value.get.return_value = mock_doc
        
        mock_db.collection.return_value = mock_collection
        
        result = get_diary_by_date("2025-01-01")
        
        assert result["date"] == "2025-01-01"
        assert result["id"] == "2025-01-01"
    
    @patch('diary_service.db')
    def test_get_diary_by_date_not_found(self, mock_db):
        """Test diary retrieval when not found"""
        from diary_service import get_diary_by_date
        
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_collection = Mock()
        mock_collection.document.return_value.get.return_value = mock_doc
        
        mock_db.collection.return_value = mock_collection
        
        result = get_diary_by_date("2025-01-01")
        
        assert result is None
    
    @patch('diary_service.db', None)
    def test_get_diary_by_date_no_db(self):
        """Test diary retrieval when db is None"""
        from diary_service import get_diary_by_date
        
        result = get_diary_by_date("2025-01-01")
        
        assert result is None


class TestCollectDailyData:
    """Tests for collect_daily_data function"""
    
    @pytest.mark.asyncio
    @patch('diary_service.get_selected_character_async')
    @patch('diary_service.get_agent_logs_for_date_async')
    @patch('diary_service.get_sensor_data_for_date_async')
    @patch('diary_service.get_current_vegetable_async')
    @patch('diary_service.get_plant_image_for_date_async')
    async def test_collect_daily_data(
        self, 
        mock_image, 
        mock_veg, 
        mock_sensor, 
        mock_agent,
        mock_character
    ):
        """Test collecting daily data"""
        from diary_service import collect_daily_data_async
        from datetime import date
        
        mock_agent.return_value = [{"action": "test"}]
        mock_sensor.return_value = [{"temperature": 25}]
        mock_veg.return_value = {"name": "Tomato"}
        mock_image.return_value = None
        mock_character.return_value = None
        
        result = await collect_daily_data_async(date(2025, 1, 1))
        
        assert result["date"] == "2025-01-01"
        assert len(result["agent_logs"]) == 1
        assert len(result["sensor_data"]) == 1
        assert result["vegetable"]["name"] == "Tomato"
        assert result["character"] is None
    
    @pytest.mark.asyncio
    @patch('diary_service.get_selected_character_async')
    @patch('diary_service.get_agent_logs_for_date_async')
    @patch('diary_service.get_sensor_data_for_date_async')
    @patch('diary_service.get_current_vegetable_async')
    @patch('diary_service.get_plant_image_for_date_async')
    async def test_collect_daily_data_with_character(
        self, 
        mock_image, 
        mock_veg, 
        mock_sensor, 
        mock_agent,
        mock_character
    ):
        """Test collecting daily data includes selected character"""
        from diary_service import collect_daily_data_async
        from datetime import date
        
        mock_agent.return_value = []
        mock_sensor.return_value = []
        mock_veg.return_value = {"name": "トマト"}
        mock_image.return_value = None
        mock_character.return_value = {
            "name": "トマちゃん",
            "personality": "元気で明るい性格",
            "image_uri": "gs://bucket/image.png"
        }
        
        result = await collect_daily_data_async(date(2025, 1, 1))
        
        assert result["character"] is not None
        assert result["character"]["name"] == "トマちゃん"
        assert result["character"]["personality"] == "元気で明るい性格"


class TestBuildDiaryPromptWithCharacter:
    """Tests for build_diary_prompt with character integration"""
    
    def test_prompt_with_character_name_and_personality(self):
        """Test prompt includes character personality when available"""
        from diary_service import build_diary_prompt
        
        statistics = {
            "temperature": {"min": 20, "max": 30, "avg": 25},
            "humidity": {"min": 50, "max": 70, "avg": 60},
            "soil_moisture": {"min": 30, "max": 40, "avg": 35}
        }
        character_info = {
            "name": "トマちゃん",
            "personality": "元気で明るい性格"
        }
        
        prompt = build_diary_prompt("2025-01-01", statistics, [], {"name": "トマト"}, character_info)
        
        assert "トマちゃん" in prompt
        assert "元気で明るい性格" in prompt
        assert "なりきって" in prompt
    
    def test_prompt_with_character_name_only(self):
        """Test prompt with character name but no personality"""
        from diary_service import build_diary_prompt
        
        statistics = {
            "temperature": {"min": 20, "max": 30, "avg": 25},
            "humidity": {"min": 50, "max": 70, "avg": 60},
            "soil_moisture": {"min": 30, "max": 40, "avg": 35}
        }
        character_info = {"name": "トマちゃん"}
        
        prompt = build_diary_prompt("2025-01-01", statistics, [], {"name": "トマト"}, character_info)
        
        assert "トマちゃん" in prompt
        assert "なりきって" in prompt
    
    def test_prompt_without_character(self):
        """Test prompt falls back to expert role when no character"""
        from diary_service import build_diary_prompt
        
        statistics = {
            "temperature": {"min": 20, "max": 30, "avg": 25},
            "humidity": {"min": 50, "max": 70, "avg": 60},
            "soil_moisture": {"min": 30, "max": 40, "avg": 35}
        }
        
        prompt = build_diary_prompt("2025-01-01", statistics, [], {"name": "トマト"}, None)
        
        assert "植物栽培の専門家" in prompt
        assert "トマちゃん" not in prompt
    
    def test_prompt_with_empty_character(self):
        """Test prompt falls back when character has no name"""
        from diary_service import build_diary_prompt
        
        statistics = {
            "temperature": {"min": 20, "max": 30, "avg": 25},
            "humidity": {"min": 50, "max": 70, "avg": 60},
            "soil_moisture": {"min": 30, "max": 40, "avg": 35}
        }
        character_info = {"image_uri": "gs://bucket/image.png"}
        
        prompt = build_diary_prompt("2025-01-01", statistics, [], {"name": "トマト"}, character_info)
        
        assert "植物栽培の専門家" in prompt


class TestGetSelectedCharacter:
    """Tests for get_selected_character_async function"""
    
    @pytest.mark.asyncio
    @patch('diary_service.db')
    async def test_get_character_success(self, mock_db):
        """Test successful character retrieval"""
        from diary_service import get_selected_character_async
        
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "name": "トマちゃん",
            "personality": "元気で明るい性格",
            "image_uri": "gs://bucket/image.png"
        }
        
        mock_collection = Mock()
        mock_collection.document.return_value.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        
        result = await get_selected_character_async()
        
        assert result is not None
        assert result["name"] == "トマちゃん"
        assert result["personality"] == "元気で明るい性格"
    
    @pytest.mark.asyncio
    @patch('diary_service.db')
    async def test_get_character_not_found(self, mock_db):
        """Test when no character is selected"""
        from diary_service import get_selected_character_async
        
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_collection = Mock()
        mock_collection.document.return_value.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        
        result = await get_selected_character_async()
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch('diary_service.db', None)
    async def test_get_character_no_db(self):
        """Test character retrieval when db is None"""
        from diary_service import get_selected_character_async
        
        result = await get_selected_character_async()
        
        assert result is None

    @pytest.mark.asyncio
    @patch('diary_service.db')
    async def test_get_character_exception(self, mock_db):
        """Test character retrieval when exception occurs"""
        from diary_service import get_selected_character_async
        mock_db.collection.side_effect = Exception("Firestore error")
        result = await get_selected_character_async()
        assert result is None


# ---------------------------------------------------------------------------
# Additional tests for 100% coverage
# ---------------------------------------------------------------------------
from datetime import date, datetime
import asyncio


class TestGetAuthHeadersAsync:
    """Tests for get_auth_headers_async (lines 29-34)"""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-key"})
    async def test_with_api_key(self):
        from diary_service import get_auth_headers_async
        headers, param = await get_auth_headers_async()
        assert param == "?key=test-key"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_without_api_key(self):
        from diary_service import get_auth_headers_async
        headers, param = await get_auth_headers_async()
        assert param == ""


class TestRequestWithRetryAsync:
    """Tests for request_with_retry_async (lines 39-61)"""

    @pytest.mark.asyncio
    async def test_success_first_attempt(self):
        from diary_service import request_with_retry_async
        import httpx
        mock_resp = Mock(spec=httpx.Response)
        mock_resp.status_code = 200
        with patch('diary_service.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client
            result = await request_with_retry_async("GET", "http://test")
            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_retry_on_429(self):
        from diary_service import request_with_retry_async
        import httpx
        resp_429 = Mock(spec=httpx.Response)
        resp_429.status_code = 429
        resp_200 = Mock(spec=httpx.Response)
        resp_200.status_code = 200
        with patch('diary_service.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=[resp_429, resp_200])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client
            with patch('diary_service.asyncio.sleep', new_callable=AsyncMock):
                result = await request_with_retry_async("GET", "http://test")
                assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_request_error_retries(self):
        from diary_service import request_with_retry_async
        import httpx
        resp_200 = Mock(spec=httpx.Response)
        resp_200.status_code = 200
        with patch('diary_service.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=[
                httpx.RequestError("err", request=Mock()),
                resp_200
            ])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client
            with patch('diary_service.asyncio.sleep', new_callable=AsyncMock):
                result = await request_with_retry_async("GET", "http://test")
                assert result.status_code == 200


class TestGetAgentLogsForDateAsync:
    """Tests for get_agent_logs_for_date_async (lines 66-95)"""

    @pytest.mark.asyncio
    @patch('diary_service.get_agent_execution_logs')
    @patch('diary_service.db', Mock())
    async def test_success_filters_by_date(self, mock_logs):
        from diary_service import get_agent_logs_for_date_async
        mock_logs.return_value = [
            {"timestamp": "2025-01-01T10:00:00Z", "data": {"action": "test"}},
            {"timestamp": "2025-01-02T10:00:00Z", "data": {"action": "other"}},
            {"timestamp": "invalid-ts", "data": {"action": "bad"}},
        ]
        result = await get_agent_logs_for_date_async(date(2025, 1, 1))
        assert len(result) == 1

    @pytest.mark.asyncio
    @patch('diary_service.db', None)
    async def test_no_db(self):
        from diary_service import get_agent_logs_for_date_async
        result = await get_agent_logs_for_date_async(date(2025, 1, 1))
        assert result == []

    @pytest.mark.asyncio
    @patch('diary_service.get_agent_execution_logs')
    @patch('diary_service.db', Mock())
    async def test_exception(self, mock_logs):
        from diary_service import get_agent_logs_for_date_async
        mock_logs.side_effect = Exception("err")
        result = await get_agent_logs_for_date_async(date(2025, 1, 1))
        assert result == []


class TestGetSensorDataForDateAsync:
    """Tests for get_sensor_data_for_date_async (lines 100-126)"""

    @pytest.mark.asyncio
    @patch('diary_service.get_sensor_history')
    @patch('diary_service.db', Mock())
    async def test_success_filters_by_date(self, mock_history):
        from diary_service import get_sensor_data_for_date_async
        from datetime import datetime as dt
        target = date(2025, 1, 1)
        ts = int(dt(2025, 1, 1, 12, 0, 0).timestamp())
        ts_other = int(dt(2025, 1, 2, 12, 0, 0).timestamp())
        mock_history.return_value = [
            {"unix_timestamp": ts, "temperature": 25},
            {"unix_timestamp": ts_other, "temperature": 20},
        ]
        result = await get_sensor_data_for_date_async(target)
        assert len(result) == 1

    @pytest.mark.asyncio
    @patch('diary_service.db', None)
    async def test_no_db(self):
        from diary_service import get_sensor_data_for_date_async
        result = await get_sensor_data_for_date_async(date(2025, 1, 1))
        assert result == []

    @pytest.mark.asyncio
    @patch('diary_service.get_sensor_history')
    @patch('diary_service.db', Mock())
    async def test_exception(self, mock_history):
        from diary_service import get_sensor_data_for_date_async
        mock_history.side_effect = Exception("err")
        result = await get_sensor_data_for_date_async(date(2025, 1, 1))
        assert result == []


class TestGetCurrentVegetableAsync:
    """Tests for get_current_vegetable_async (lines 144-151)"""

    @pytest.mark.asyncio
    @patch('diary_service.get_latest_vegetable')
    @patch('diary_service.get_edge_agent_config')
    async def test_from_config(self, mock_config, mock_latest):
        from diary_service import get_current_vegetable_async
        mock_config.return_value = {"vegetable_name": "Tomato"}
        result = await get_current_vegetable_async()
        assert result["name"] == "Tomato"
        mock_latest.assert_not_called()

    @pytest.mark.asyncio
    @patch('diary_service.get_latest_vegetable')
    @patch('diary_service.get_edge_agent_config')
    async def test_fallback_to_latest(self, mock_config, mock_latest):
        from diary_service import get_current_vegetable_async
        mock_config.return_value = {}
        mock_latest.return_value = {"name": "Cucumber"}
        result = await get_current_vegetable_async()
        assert result["name"] == "Cucumber"

    @pytest.mark.asyncio
    @patch('diary_service.get_edge_agent_config')
    async def test_exception(self, mock_config):
        from diary_service import get_current_vegetable_async
        mock_config.side_effect = Exception("err")
        result = await get_current_vegetable_async()
        assert result is None


class TestGetPlantImageForDateAsync:
    """Tests for get_plant_image_for_date_async"""

    @pytest.mark.asyncio
    async def test_returns_none(self):
        from diary_service import get_plant_image_for_date_async
        result = await get_plant_image_for_date_async(date(2025, 1, 1))
        assert result is None


class TestGenerateDiaryWithAiAsync:
    """Tests for generate_diary_with_ai_async (lines 335-371)"""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_no_api_key(self):
        from diary_service import generate_diary_with_ai_async
        result = await generate_diary_with_ai_async("2025-01-01", {}, [], None)
        assert "API Key" in result["summary"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-key"})
    async def test_success(self):
        from diary_service import generate_diary_with_ai_async
        import httpx
        mock_resp = Mock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"summary": "Good day", "observations": "Growing", "recommendations": "Water"}'
                    }]
                }
            }]
        }
        mock_resp.text = ""
        with patch('diary_service.request_with_retry_async', new_callable=AsyncMock, return_value=mock_resp):
            stats = {"temperature": {"min": 20, "max": 30, "avg": 25}, "humidity": {"min": 50, "max": 60, "avg": 55}, "soil_moisture": {"min": 30, "max": 40, "avg": 35}}
            result = await generate_diary_with_ai_async("2025-01-01", stats, [], {"name": "Tomato"})
            assert result["summary"] == "Good day"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-key"})
    async def test_api_error(self):
        from diary_service import generate_diary_with_ai_async
        import httpx
        mock_resp = Mock(spec=httpx.Response)
        mock_resp.status_code = 500
        mock_resp.text = "Server Error"
        with patch('diary_service.request_with_retry_async', new_callable=AsyncMock, return_value=mock_resp):
            stats = {"temperature": {"min": 0, "max": 0, "avg": 0}, "humidity": {"min": 0, "max": 0, "avg": 0}, "soil_moisture": {"min": 0, "max": 0, "avg": 0}}
            result = await generate_diary_with_ai_async("2025-01-01", stats, [], None)
            assert "500" in result["summary"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-key"})
    async def test_exception_during_api_call(self):
        from diary_service import generate_diary_with_ai_async
        with patch('diary_service.request_with_retry_async', new_callable=AsyncMock, side_effect=Exception("network")):
            stats = {"temperature": {"min": 0, "max": 0, "avg": 0}, "humidity": {"min": 0, "max": 0, "avg": 0}, "soil_moisture": {"min": 0, "max": 0, "avg": 0}}
            result = await generate_diary_with_ai_async("2025-01-01", stats, [], None)
            assert "エラー" in result["summary"]


class TestInitDiaryStatusAsync:
    """Tests for init_diary_status_async"""

    @pytest.mark.asyncio
    @patch('diary_service.db')
    async def test_success(self, mock_db):
        from diary_service import init_diary_status_async
        mock_col = Mock()
        mock_doc = Mock()
        mock_col.document.return_value = mock_doc
        mock_db.collection.return_value = mock_col
        await init_diary_status_async("2025-01-01")
        mock_doc.set.assert_called_once()

    @pytest.mark.asyncio
    @patch('diary_service.db', None)
    async def test_no_db(self):
        from diary_service import init_diary_status_async
        await init_diary_status_async("2025-01-01")  # no error

    @pytest.mark.asyncio
    @patch('diary_service.db')
    async def test_exception(self, mock_db):
        from diary_service import init_diary_status_async
        mock_db.collection.side_effect = Exception("err")
        await init_diary_status_async("2025-01-01")  # no raise


class TestSaveDiaryAsync:
    """Tests for save_diary_async"""

    @pytest.mark.asyncio
    @patch('diary_service.db')
    async def test_success(self, mock_db):
        from diary_service import save_diary_async
        mock_col = Mock()
        mock_doc = Mock()
        mock_col.document.return_value = mock_doc
        mock_db.collection.return_value = mock_col
        await save_diary_async("2025-01-01", {"data": "test"})
        mock_doc.set.assert_called_once()

    @pytest.mark.asyncio
    @patch('diary_service.db', None)
    async def test_no_db(self):
        from diary_service import save_diary_async
        await save_diary_async("2025-01-01", {})

    @pytest.mark.asyncio
    @patch('diary_service.db')
    async def test_exception(self, mock_db):
        from diary_service import save_diary_async
        mock_db.collection.side_effect = Exception("err")
        await save_diary_async("2025-01-01", {})


class TestMarkDiaryFailedAsync:
    """Tests for mark_diary_failed_async"""

    @pytest.mark.asyncio
    @patch('diary_service.db')
    async def test_success(self, mock_db):
        from diary_service import mark_diary_failed_async
        mock_col = Mock()
        mock_doc = Mock()
        mock_col.document.return_value = mock_doc
        mock_db.collection.return_value = mock_col
        await mark_diary_failed_async("2025-01-01", "error message")
        mock_doc.update.assert_called_once()

    @pytest.mark.asyncio
    @patch('diary_service.db', None)
    async def test_no_db(self):
        from diary_service import mark_diary_failed_async
        await mark_diary_failed_async("2025-01-01", "err")

    @pytest.mark.asyncio
    @patch('diary_service.db')
    async def test_exception(self, mock_db):
        from diary_service import mark_diary_failed_async
        mock_db.collection.side_effect = Exception("err")
        await mark_diary_failed_async("2025-01-01", "err")


class TestProcessDailyDiary:
    """Tests for process_daily_diary (lines 444-508)"""

    @pytest.mark.asyncio
    @patch('diary_service.mark_diary_failed_async', new_callable=AsyncMock)
    @patch('diary_service.save_diary_async', new_callable=AsyncMock)
    @patch('diary_service.init_diary_status_async', new_callable=AsyncMock)
    @patch('diary_service.generate_picture_diary', return_value="gs://bucket/img.png")
    @patch('diary_service.generate_diary_with_ai_async', new_callable=AsyncMock)
    @patch('diary_service.collect_daily_data_async', new_callable=AsyncMock)
    async def test_success(self, mock_collect, mock_generate, mock_picture, mock_init, mock_save, mock_fail):
        from diary_service import process_daily_diary
        mock_collect.return_value = {
            "date": "2025-01-01",
            "agent_logs": [],
            "sensor_data": [{"temperature": 25}],
            "vegetable": {"name": "Tomato", "id": "v1"},
            "character": None,
            "plant_image": None,
        }
        mock_generate.return_value = {
            "summary": "Good day",
            "observations": "Growing",
            "recommendations": "Water",
        }
        progress = []
        await process_daily_diary("2025-01-01", progress_callback=lambda m: progress.append(m))
        mock_save.assert_called_once()

    @pytest.mark.asyncio
    @patch('diary_service.mark_diary_failed_async', new_callable=AsyncMock)
    @patch('diary_service.init_diary_status_async', new_callable=AsyncMock)
    @patch('diary_service.collect_daily_data_async', new_callable=AsyncMock)
    async def test_failure(self, mock_collect, mock_init, mock_fail):
        from diary_service import process_daily_diary
        mock_collect.side_effect = Exception("data error")
        await process_daily_diary("2025-01-01")
        mock_fail.assert_called_once()

    @pytest.mark.asyncio
    @patch('diary_service.mark_diary_failed_async', new_callable=AsyncMock)
    @patch('diary_service.save_diary_async', new_callable=AsyncMock)
    @patch('diary_service.init_diary_status_async', new_callable=AsyncMock)
    @patch('diary_service.generate_picture_diary', side_effect=Exception("img error"))
    @patch('diary_service.generate_diary_with_ai_async', new_callable=AsyncMock)
    @patch('diary_service.collect_daily_data_async', new_callable=AsyncMock)
    async def test_image_generation_fails(self, mock_collect, mock_generate, mock_picture, mock_init, mock_save, mock_fail):
        from diary_service import process_daily_diary
        mock_collect.return_value = {
            "date": "2025-01-01",
            "agent_logs": [],
            "sensor_data": [],
            "vegetable": {"name": "Tomato", "id": "v1"},
            "character": None,
            "plant_image": None,
        }
        mock_generate.return_value = {"summary": "S", "observations": "O", "recommendations": "R"}
        await process_daily_diary("2025-01-01")
        mock_save.assert_called_once()  # should still save even if image fails


class TestCollectDailyDataWithProgressCallback:
    """Tests for collect_daily_data_async with sync progress_callback"""

    @pytest.mark.asyncio
    @patch('diary_service.get_selected_character_async', new_callable=AsyncMock, return_value=None)
    @patch('diary_service.get_plant_image_for_date_async', new_callable=AsyncMock, return_value=None)
    @patch('diary_service.get_current_vegetable_async', new_callable=AsyncMock, return_value={"name": "T"})
    @patch('diary_service.get_sensor_data_for_date_async', new_callable=AsyncMock, return_value=[])
    @patch('diary_service.get_agent_logs_for_date_async', new_callable=AsyncMock, return_value=[])
    async def test_with_sync_callback(self, *mocks):
        from diary_service import collect_daily_data_async
        messages = []
        def sync_cb(msg):
            messages.append(msg)
        result = await collect_daily_data_async(date(2025, 1, 1), progress_callback=sync_cb)
        assert len(messages) > 0


class TestGetAllDiariesAdditional:
    """Additional tests for get_all_diaries"""

    @patch('diary_service.db')
    def test_with_datetime_conversion(self, mock_db):
        from diary_service import get_all_diaries
        dt = datetime(2025, 1, 1, 10, 0, 0)
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {"date": "2025-01-01", "created_at": dt, "generation_status": "completed"}
        mock_doc.id = "2025-01-01"
        mock_query = Mock()
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = [mock_doc]
        mock_collection = Mock()
        mock_collection.where.return_value = mock_query
        mock_db.collection.return_value = mock_collection
        result = get_all_diaries()
        assert result[0]["created_at"] == dt.isoformat()

    @patch('diary_service.db')
    def test_with_offset(self, mock_db):
        from diary_service import get_all_diaries
        mock_query = Mock()
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.stream.return_value = []
        mock_collection = Mock()
        mock_collection.where.return_value = mock_query
        mock_db.collection.return_value = mock_collection
        result = get_all_diaries(limit=10, offset=5)
        assert result == []

    @patch('diary_service.db')
    def test_exception(self, mock_db):
        from diary_service import get_all_diaries
        mock_db.collection.side_effect = Exception("err")
        result = get_all_diaries()
        assert result == []


class TestGetDiaryByDateAdditional:
    """Additional tests for get_diary_by_date"""

    @patch('diary_service.db')
    def test_with_datetime_conversion(self, mock_db):
        from diary_service import get_diary_by_date
        dt = datetime(2025, 1, 1, 10, 0, 0)
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"date": "2025-01-01", "created_at": dt}
        mock_doc.id = "2025-01-01"
        mock_collection = Mock()
        mock_collection.document.return_value.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        result = get_diary_by_date("2025-01-01")
        assert result["created_at"] == dt.isoformat()

    @patch('diary_service.db')
    def test_exception(self, mock_db):
        from diary_service import get_diary_by_date
        mock_db.collection.side_effect = Exception("err")
        result = get_diary_by_date("2025-01-01")
        assert result is None


class TestExtractKeyEventsAdditional:
    """Additional event types"""

    def test_warning_event(self):
        from diary_service import extract_key_events
        logs = [{"timestamp": "T", "data": {"comment": "注意: 水不足"}}]
        events = extract_key_events(logs)
        assert events[0]["type"] == "warning"

    def test_info_event(self):
        from diary_service import extract_key_events
        logs = [{"timestamp": "T", "data": {"comment": "通常稼働中"}}]
        events = extract_key_events(logs)
        assert events[0]["type"] == "info"

    def test_string_operation_action(self):
        from diary_service import extract_key_events
        logs = [{"timestamp": "T", "data": {"operation": {"pump": "ON"}}}]
        events = extract_key_events(logs)
        assert events[0]["action"] == "ON"


class TestParseDiaryResponseMarkdown:
    """Additional parse tests"""

    def test_parse_with_triple_backticks_no_json(self):
        from diary_service import parse_diary_response
        text = '```\n{"summary": "S", "observations": "O", "recommendations": "R"}\n```'
        result = parse_diary_response(text)
        assert result["summary"] == "S"


# ---------------------------------------------------------------------------
# Additional coverage: L60-61, L379, L448
# ---------------------------------------------------------------------------

class TestHttpRetryRequestError:
    """Cover L60-61: httpx.RequestError retry in request_with_retry_async."""

    @pytest.mark.asyncio
    async def test_request_error_triggers_retry(self):
        """Cover L55-57 (RequestError branch): request fails then succeeds."""
        from backend.diary_service import request_with_retry_async
        import httpx

        call_count = 0

        async def mock_request(method, url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.RequestError("Connection refused")
            # Second attempt succeeds
            resp = httpx.Response(200, text="ok")
            return resp

        with patch('httpx.AsyncClient') as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.request = mock_request
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            with patch('backend.diary_service.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await request_with_retry_async("GET", "http://test.com")
                assert result.status_code == 200
                mock_sleep.assert_called()


class TestSyncProgressCallback:
    """Cover L379 and L448: non-coroutine progress_callback branch."""

    @pytest.mark.asyncio
    async def test_collect_daily_data_sync_callback(self):
        """Cover L379: progress_callback is a regular function (not coroutine)."""
        from backend.diary_service import collect_daily_data_async
        from datetime import date

        messages = []
        def sync_callback(msg):
            messages.append(msg)

        with patch('backend.diary_service.get_agent_logs_for_date_async', new_callable=AsyncMock, return_value=[]):
            with patch('backend.diary_service.get_sensor_data_for_date_async', new_callable=AsyncMock, return_value=[]):
                with patch('backend.diary_service.get_current_vegetable_async', new_callable=AsyncMock, return_value=None):
                    with patch('backend.diary_service.get_selected_character_async', new_callable=AsyncMock, return_value=None):
                        with patch('backend.diary_service.get_plant_image_for_date_async', new_callable=AsyncMock, return_value=None):
                            result = await collect_daily_data_async(date(2025, 1, 1), progress_callback=sync_callback)
                            assert len(messages) > 0  # sync callback was invoked

    @pytest.mark.asyncio
    async def test_process_daily_diary_sync_callback(self):
        """Cover L448: progress_callback is a regular function in process_daily_diary."""
        from backend.diary_service import process_daily_diary

        messages = []
        def sync_callback(msg):
            messages.append(msg)

        with patch('backend.diary_service.collect_daily_data_async', new_callable=AsyncMock) as mock_collect:
            mock_collect.return_value = {
                "date": "2025-01-01",
                "agent_logs": [],
                "sensor_data": [],
                "vegetable": {"name": "Tomato", "id": "t1"},
                "character": None,
                "plant_image": None,
            }
            with patch('backend.diary_service.generate_diary_with_ai_async', new_callable=AsyncMock) as mock_gen:
                mock_gen.return_value = {
                    "summary": "Test summary",
                    "observations": "Obs",
                    "recommendations": "Rec",
                }
                with patch('backend.diary_service.generate_picture_diary', return_value="http://img.png"):
                    with patch('backend.diary_service.save_diary_async', new_callable=AsyncMock):
                        with patch('backend.diary_service.init_diary_status_async', new_callable=AsyncMock):
                            await process_daily_diary("2025-01-01", progress_callback=sync_callback)
                            assert len(messages) > 0  # sync callback was invoked
