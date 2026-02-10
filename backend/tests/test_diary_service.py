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
