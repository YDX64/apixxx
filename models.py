"""
Data models, validation schemas, and custom exceptions
"""
from marshmallow import Schema, fields, ValidationError

# --- Custom Exceptions ---

class APIError(Exception):
    """Custom API Exception"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

# --- Validation Schemas ---

class MatchRequestSchema(Schema):
    """Schema for match request validation"""
    match_id = fields.Integer(
        required=True, 
        validate=lambda x: x > 0, 
        error_messages={'invalid': 'Match ID must be a positive integer'}
    )

class DateRequestSchema(Schema):
    """Schema for date-based requests"""
    date = fields.Date(
        required=True,
        error_messages={'invalid': 'Date must be in YYYY-MM-DD format'}
    )

class TokenRequestSchema(Schema):
    """Schema for token generation requests"""
    api_key = fields.String(
        required=True,
        validate=lambda x: len(x) > 0,
        error_messages={'invalid': 'API key cannot be empty'}
    )

# --- Data Models ---

class MatchInfo:
    """Match information data model"""
    def __init__(self, match_id, home_team, away_team, league=None, match_time=None, score_info=None):
        self.match_id = match_id
        self.home_team = home_team
        self.away_team = away_team
        self.league = league
        self.match_time = match_time
        self.score_info = score_info or {}
    
    def to_dict(self):
        return {
            'match_id': self.match_id,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'league': self.league,
            'match_time': self.match_time.isoformat() if self.match_time else None,
            'score_info': self.score_info
        }

class LeagueInfo:
    """League information data model"""
    def __init__(self, league_id, league_name, league_code=None, color=None):
        self.league_id = league_id
        self.league_name = league_name
        self.league_code = league_code
        self.color = color
    
    def to_dict(self):
        return {
            'id': self.league_id,
            'name': self.league_name,
            'code': self.league_code,
            'color': self.color
        }

class APIResponse:
    """Standardized API response model"""
    def __init__(self, data=None, error=None, status_code=200, cached=False):
        self.data = data
        self.error = error
        self.status_code = status_code
        self.cached = cached
        self.timestamp = None
    
    def to_dict(self):
        response = {}
        if self.data is not None:
            response['data'] = self.data
        if self.error:
            response['error'] = self.error
        if self.cached:
            response['cached'] = True
        if self.timestamp:
            response['timestamp'] = self.timestamp
        return response

# --- Validation Helper Functions ---

def validate_match_id(match_id):
    """Validate match ID parameter"""
    if not isinstance(match_id, int) or match_id <= 0:
        raise APIError("Invalid match ID. Must be a positive integer.", 400)
    return match_id

def validate_date_string(date_str):
    """Validate date string format"""
    from datetime import datetime
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj
    except ValueError:
        raise APIError("Invalid date format. Use YYYY-MM-DD", 400)

def validate_api_key(api_key):
    """Validate API key format"""
    if not api_key or not isinstance(api_key, str) or len(api_key.strip()) == 0:
        raise APIError("Invalid API key", 400)
    return api_key.strip()

# --- Response Builders ---

def build_success_response(data, cached=False, extra_fields=None):
    """Build successful API response"""
    from datetime import datetime
    
    response = {
        'data': data,
        'timestamp': datetime.utcnow().isoformat(),
        'success': True
    }
    
    if cached:
        response['cached'] = True
    
    if extra_fields:
        response.update(extra_fields)
    
    return response

def build_error_response(message, status_code=400, details=None):
    """Build error API response"""
    from datetime import datetime
    
    response = {
        'error': message,
        'timestamp': datetime.utcnow().isoformat(),
        'success': False
    }
    
    if details:
        response['details'] = details
    
    return response

# --- Schema Instances ---
match_request_schema = MatchRequestSchema()
date_request_schema = DateRequestSchema()
token_request_schema = TokenRequestSchema()
