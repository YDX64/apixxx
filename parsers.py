"""
Data parsing utilities for match information
"""
import re
import json
import logging
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class MatchDateParser:
    """Parser for date-based match data from JavaScript responses"""
    
    def __init__(self):
        self.leagues = {}  # B dizisi cache
        self.countries = {}  # C dizisi cache
    
    def parse_date_response(self, response_text):
        """date.txt formatındaki veriyi parse et"""
        try:
            # JSON içindeki JavaScript kodunu çıkar
            json_data = json.loads(response_text)
            js_code = json_data.get('Data', '')
            
            # A, B, C dizilerini parse et
            matches = self._parse_matches(js_code)
            leagues = self._parse_leagues(js_code)
            countries = self._parse_countries(js_code)
            
            return {
                'matches': matches,
                'leagues': leagues,
                'countries': countries
            }
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None
    
    def _parse_matches(self, js_code):
        """A dizisini parse et - maç bilgileri"""
        matches = []
        
        # A[n]=[...] formatındaki satırları bul
        pattern = r"A\[(\d+)\]=\[(.*?)\];"
        
        for match in re.finditer(pattern, js_code):
            try:
                index = int(match.group(1))
                data_str = match.group(2)
                
                # Veriyi parse et
                match_data = self._parse_match_data(data_str)
                if match_data:
                    matches.append(match_data)
                    
            except Exception as e:
                logger.warning(f"Match parse error for index {index}: {e}")
                continue
        
        return matches
    
    def _parse_match_data(self, data_str):
        """Tek maç verisini parse et"""
        try:
            # JavaScript array parsing
            parts = []
            current = ""
            in_quotes = False
            
            for char in data_str:
                if char == "'" and not in_quotes:
                    in_quotes = True
                elif char == "'" and in_quotes:
                    in_quotes = False
                    parts.append(current)
                    current = ""
                elif char == "," and not in_quotes:
                    if current.strip():
                        parts.append(current.strip())
                    current = ""
                else:
                    current += char
            
            if current.strip():
                parts.append(current.strip())
            
            # En az 7 alan olmalı
            if len(parts) < 7:
                return None
            
            # Tarih parse et
            datetime_str = parts[6] if len(parts) > 6 else ""
            match_time = self._parse_datetime(datetime_str)
            
            return {
                'match_id': int(parts[0]) if parts[0].isdigit() else None,
                'league_id': int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None,
                'home_team_id': int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None,
                'away_team_id': int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else None,
                'home_team': parts[4] if len(parts) > 4 else "",
                'away_team': parts[5] if len(parts) > 5 else "",
                'match_time': match_time,
                'match_datetime_raw': datetime_str
            }
            
        except Exception as e:
            logger.error(f"Match data parse error: {e}")
            return None
    
    def _parse_datetime(self, datetime_str):
        """2025,7,24,13,00,00 formatını parse et"""
        try:
            # Virgül ile ayrılmış formatı parse et
            parts = datetime_str.split(',')
            if len(parts) >= 6:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                hour = int(parts[3])
                minute = int(parts[4])
                second = int(parts[5])
                
                return datetime(year, month, day, hour, minute, second)
        except:
            pass
        
        return None
    
    def _parse_leagues(self, js_code):
        """B dizisini parse et - lig bilgileri"""
        leagues = {}
        pattern = r"B\[(\d+)\]=\[(.*?)\];"
        
        for match in re.finditer(pattern, js_code):
            try:
                index = int(match.group(1))
                data_str = match.group(2)
                
                # Basit parse
                parts = [p.strip().strip("'\"") for p in data_str.split(',')]
                if len(parts) >= 3:
                    leagues[index] = {
                        'league_id': parts[0],
                        'league_code': parts[1],
                        'league_name': parts[2],
                        'color': parts[3] if len(parts) > 3 else None
                    }
            except:
                continue
        
        return leagues
    
    def _parse_countries(self, js_code):
        """C dizisini parse et - ülke bilgileri"""
        countries = {}
        pattern = r"C\[(\d+)\]=\[(.*?)\];"
        
        for match in re.finditer(pattern, js_code):
            try:
                index = int(match.group(1))
                data_str = match.group(2)
                
                parts = [p.strip().strip("'\"") for p in data_str.split(',')]
                if len(parts) >= 2:
                    countries[index] = {
                        'country_id': parts[0],
                        'country_name': parts[1]
                    }
            except:
                continue
        
        return countries


# --- HTML Parsing Functions ---

def clean_score_data(text):
    """Clean score data by removing parentheses and extra whitespace"""
    if not text:
        return ""
    
    # Remove parentheses and clean whitespace
    cleaned = text.strip()
    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = cleaned[1:-1]  # Remove outer parentheses
    
    return cleaned.strip()

def debug_table_structure(soup, table_id):
    """Debug function to analyze table structure"""
    table = soup.find('table', id=table_id)
    if not table:
        return {"error": f"Table with id '{table_id}' not found"}
    
    debug_info = {
        "table_id": table_id,
        "total_rows": 0,
        "sample_row_structure": []
    }
    
    data_rows = table.find_all('tr', id=re.compile(r"tr\d+_\d+"))
    debug_info["total_rows"] = len(data_rows)
    
    # Analyze first few rows
    for i, row in enumerate(data_rows[:3]):  # First 3 rows
        cells = row.find_all('td')
        row_structure = {
            "row_index": i,
            "cell_count": len(cells),
            "cells": []
        }
        
        for j, cell in enumerate(cells):
            cell_info = {
                "index": j,
                "text": cell.text.strip()[:50] + "..." if len(cell.text.strip()) > 50 else cell.text.strip(),
                "has_spans": len(cell.find_all('span')) > 0,
                "span_classes": [span.get('class', []) for span in cell.find_all('span')]
            }
            row_structure["cells"].append(cell_info)
        
        debug_info["sample_row_structure"].append(row_structure)
    
    return debug_info

def parse_player_list(container):
    """Helper function to parse a list of players from a container."""
    if not container:
        return []
    player_list = []
    player_rows = container.find_all('div', class_='player-row')
    for player_row in player_rows:
        player_data = {
            "player_id": player_row.get("playerid"),
            "position": player_row.find('b').text.strip() if player_row.find('b') else "",
            "number": player_row.find('span').text.strip() if player_row.find('span') else "",
            "name": player_row.find('a').text.strip() if player_row.find('a') else ""
        }
        player_list.append(player_data)
    return player_list

def parse_standings_table(table):
    """Parses a standings table into a structured dictionary."""
    data = {"full_time": [], "half_time": []}
    all_rows = table.find_all('tr')
    def parse_block(rows_block):
        parsed_data = []
        if not rows_block or len(rows_block) < 2:
            return parsed_data
        headers = [th.text.strip() for th in rows_block[0].find_all('th')]
        for data_row in rows_block[1:]:
            cells = data_row.find_all('td')
            if len(cells) == len(headers):
                row_data = {headers[i]: cells[i].text.strip() for i in range(len(headers))}
                parsed_data.append(row_data)
        return parsed_data
    split_index = -1
    for i, row in enumerate(all_rows):
        if "HT" in row.text and row.find('th'):
            split_index = i
            break
    if split_index != -1:
        ft_rows = all_rows[2:split_index]
        ht_rows = all_rows[split_index+1:]
        ft_headers_row = all_rows[1]
        ht_headers_row = all_rows[split_index]
        data["full_time"] = parse_block([ft_headers_row] + ft_rows)
        data["half_time"] = parse_block([ht_headers_row] + ht_rows)
    return data

def parse_match_list_table(soup, table_id):
    """Parse match list table with given ID"""
    table = soup.find('table', id=table_id)
    if not table:
        return []
    rows = []
    data_rows = table.find_all('tr', id=re.compile(r"tr\d+_\d+"))
    for row in data_rows:
        cells = row.find_all('td')
        if len(cells) < 8:
            continue
        
        # Get score cells with fallback
        score_cell = cells[3].find('span', class_=re.compile(r"fscore_"))
        ht_score_cell = cells[3].find('span', class_=re.compile(r"hscore_"))
        corner_cell = cells[5].find('span', class_=re.compile(r"fcorner_"))
        ht_corner_cell = cells[5].find('span', class_=re.compile(r"hcorner_"))
        
        # Extract date - try multiple approaches
        date_text = ""
        if len(cells) > 1:
            # Try direct text first
            date_text = cells[1].text.strip()
            # If empty, try looking for nested elements
            if not date_text:
                date_element = cells[1].find('span') or cells[1].find('a')
                if date_element:
                    date_text = date_element.text.strip()
        
        # Extract result - try multiple positions and approaches
        result_text = ""
        if len(cells) > 11:
            result_text = cells[11].text.strip()
        elif len(cells) > 7:
            result_text = cells[7].text.strip()
        
        # If still empty, try looking in other cells or nested elements
        if not result_text:
            for cell_idx in [6, 7, 8, 9, 10, 11]:
                if len(cells) > cell_idx:
                    potential_result = cells[cell_idx].text.strip()
                    if potential_result and potential_result not in ['', '-', '?']:
                        result_text = potential_result
                        break
        
        row_data = {
            "league": cells[0].text.strip() if len(cells) > 0 else "",
            "date": date_text,
            "home_team": cells[2].text.strip() if len(cells) > 2 else "",
            "score": clean_score_data(score_cell.text) if score_cell else "",
            "ht_score": clean_score_data(ht_score_cell.text) if ht_score_cell else "",
            "away_team": cells[4].text.strip() if len(cells) > 4 else "",
            "corner": clean_score_data(corner_cell.text) if corner_cell else "",
            "ht_corner": clean_score_data(ht_corner_cell.text) if ht_corner_cell else "",
            "result": result_text
        }
        rows.append(row_data)
    return rows

def parse_standings(soup):
    """Parse team standings from soup"""
    standings = {}
    standings_parent_div = soup.find('div', id='porletP4')
    if not standings_parent_div:
        return standings
    home_div = standings_parent_div.find('div', class_='home-div')
    guest_div = standings_parent_div.find('div', class_='guest-div')
    if home_div:
        home_table = home_div.find('table', class_='team-table-home')
        if home_table:
            standings['home_team_standings'] = parse_standings_table(home_table)
    if guest_div:
        guest_table = guest_div.find('table', class_='team-table-guest')
        if guest_table:
            standings['away_team_standings'] = parse_standings_table(guest_table)
    return standings

def parse_injury_suspension(soup):
    """Parse injury and suspension data"""
    injury_section = soup.find('div', id='porletP13')
    if not injury_section:
        return {"error": "Injury and Suspension section (porletP13) not found."}
    data = {"home_team": [], "away_team": []}
    home_div = injury_section.find('div', id='injuryH')
    if home_div:
        data["home_team"] = parse_player_list(home_div.find('div', class_='player-list'))
    guest_div = injury_section.find('div', id='injuryG')
    if guest_div:
        data["away_team"] = parse_player_list(guest_div.find('div', class_='player-list'))
    return data

def parse_last_match_lineups(soup):
    """Parse last match lineups"""
    lineup_section = soup.find('div', id='porletP14')
    if not lineup_section:
        return {"error": "Last Match Lineups section (porletP14) not found."}
    data = {"home_team": {}, "away_team": {}}
    home_div = lineup_section.find('div', id='lineupH')
    if home_div:
        formation = home_div.find('div', class_='injury').text.strip() if home_div.find('div', class_='injury') else ""
        player_lists = home_div.find_all('div', class_='player-list')
        starters = parse_player_list(player_lists[0]) if len(player_lists) > 0 else []
        substitutes = parse_player_list(player_lists[1]) if len(player_lists) > 1 else []
        data["home_team"] = {"formation": formation, "starters": starters, "substitutes": substitutes}
    guest_div = lineup_section.find('div', id='lineupG')
    if guest_div:
        formation = guest_div.find('div', class_='injury').text.strip() if guest_div.find('div', class_='injury') else ""
        player_lists = guest_div.find_all('div', class_='player-list')
        starters = parse_player_list(player_lists[0]) if len(player_lists) > 0 else []
        substitutes = parse_player_list(player_lists[1]) if len(player_lists) > 1 else []
        data["away_team"] = {"formation": formation, "starters": starters, "substitutes": substitutes}
    return data

def parse_fixture(soup):
    """Parse fixture data"""
    fixture_section = soup.find('div', id='porletP12')
    if not fixture_section:
        return {"error": "Fixture section (porletP12) not found."}
    data = {"home_team_fixture": [], "away_team_fixture": []}
    def parse_fixture_table(table):
        fixtures = []
        if not table:
            return fixtures
        rows = table.find_all('tr')[1:]
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 5:
                fixtures.append({
                    "league": cells[0].get('title', ''),
                    "date": cells[1].text.strip(),
                    "type": cells[2].text.strip(),
                    "opponent": cells[3].text.strip(),
                    "countdown": cells[4].text.strip()
                })
        return fixtures
    home_div = fixture_section.find('div', class_='home-div')
    if home_div:
        data["home_team_fixture"] = parse_fixture_table(home_div.find('table'))
    guest_div = fixture_section.find('div', class_='guest-div')
    if guest_div:
        data["away_team_fixture"] = parse_fixture_table(guest_div.find('table'))
    return data

def parse_match_info(soup):
    """Parse match header information"""
    header = soup.find('div', id='fbheader')
    if not header:
        return {"error": "Match info header (fbheader) not found."}

    def get_logo_url(img_tag):
        if not img_tag: return ""
        src = img_tag.get('src', '')
        return f"https:{src}" if src.startswith('//') else src

    home_team_div = header.find('div', class_='home')
    guest_team_div = header.find('div', class_='guest')
    other_info_div = header.find('div', id='otherInfo')
    
    league_text = ""
    league_span = header.find('span', class_='sclassLink')
    if league_span:
        league_text = ' '.join(league_span.text.split())

    stadium = ""
    weather = ""
    if other_info_div:
        stadium_icon = other_info_div.find('i', class_='icon-font-animation')
        if stadium_icon and stadium_icon.parent:
            stadium = stadium_icon.parent.text.strip()
        weather_icon = other_info_div.find('i', class_='icon-weather')
        if weather_icon and weather_icon.next_sibling:
            weather = str(weather_icon.next_sibling).strip()

    # Score parsing logic
    score_info = {
        "status": "",
        "home_score": "",
        "away_score": "",
        "ht_score": "",
        "ht_home_score": "",
        "ht_away_score": ""
    }
    
    score_container = header.find('div', id='mScore')
    if score_container:
        state_div = score_container.find('div', class_='state')
        if state_div:
            score_info["status"] = state_div.text.strip()

        scores = score_container.find_all('div', class_='score')
        if len(scores) == 2:
            score_info["home_score"] = scores[0].text.strip()
            score_info["away_score"] = scores[1].text.strip()

        ht_score_span = score_container.find('span', title='Score 1st Half')
        if ht_score_span:
            ht_score_full = ht_score_span.text.strip()
            score_info["ht_score"] = ht_score_full
            if '-' in ht_score_full:
                parts = ht_score_full.split('-')
                score_info["ht_home_score"] = parts[0]
                score_info["ht_away_score"] = parts[1]


    return {
        "league": league_text,
        "match_time_utc": header.find('span', class_='time').get('data-t', '') if header.find('span', class_='time') else "",
        "home_team_name": home_team_div.find('div', class_='sclassName').text.strip() if home_team_div and home_team_div.find('div', class_='sclassName') else "",
        "home_team_logo_url": get_logo_url(home_team_div.find('img')) if home_team_div else "",
        "away_team_name": guest_team_div.find('div', class_='sclassName').text.strip() if guest_team_div and guest_team_div.find('div', class_='sclassName') else "",
        "away_team_logo_url": get_logo_url(guest_team_div.find('img')) if guest_team_div else "",
        "stadium": stadium,
        "weather": weather,
        "score_info": score_info
    }

def parse_first_half_odds(json_data):
    """Parse first half odds JSON data"""
    try:
        if not json_data or not isinstance(json_data, dict):
            return {"error": "Invalid JSON data for first half odds"}
        
        # Extract main data structure
        error_code = json_data.get('ErrCode', -1)
        data = json_data.get('Data', {})
        match_state = json_data.get('MatchState', -1)
        
        if error_code != 0:
            return {"error": f"API returned error code: {error_code}"}
        
        # Parse mixodds (betting company odds)
        mixodds = data.get('mixodds', [])
        parsed_odds = []
        
        for odds_entry in mixodds:
            try:
                company_data = {
                    "company_id": odds_entry.get('cid'),
                    "company_name": odds_entry.get('cn', ''),
                    "european_odds": {
                        "first": odds_entry.get('euro', {}).get('f', {}),
                        "last": odds_entry.get('euro', {}).get('l', {}),
                        "current": odds_entry.get('euro', {}).get('r', {}),
                        "has_changed": odds_entry.get('euro', {}).get('hr', False)
                    },
                    "over_under": {
                        "first": odds_entry.get('ou', {}).get('f', {}),
                        "last": odds_entry.get('ou', {}).get('l', {}),
                        "current": odds_entry.get('ou', {}).get('r', {}),
                        "has_changed": odds_entry.get('ou', {}).get('hr', False)
                    },
                    "asian_handicap": {
                        "first": odds_entry.get('ah', {}).get('f', {}),
                        "last": odds_entry.get('ah', {}).get('l', {}),
                        "current": odds_entry.get('ah', {}).get('r', {}),
                        "has_changed": odds_entry.get('ah', {}).get('hr', False)
                    }
                }
                parsed_odds.append(company_data)
            except Exception as e:
                logger.warning(f"Error parsing odds entry: {e}")
                continue
        
        return {
            "error_code": error_code,
            "match_state": match_state,
            "betting_companies_count": len(parsed_odds),
            "first_half_odds": parsed_odds,
            "raw_data_preview": {
                "total_companies": len(mixodds),
                "data_keys": list(data.keys()) if data else []
            }
        }
        
    except Exception as e:
        logger.error(f"Error parsing first half odds: {e}")
        return {"error": f"Failed to parse first half odds: {str(e)}"}

def parse_h2h_details(soup):
    """Parses the h2h details from a soup object."""
    details = {}
    details['standings'] = parse_standings(soup)
    details['head_to_head'] = parse_match_list_table(soup, 'table_v3')
    details['home_team_previous_matches'] = parse_match_list_table(soup, 'table_v1')
    details['away_team_previous_matches'] = parse_match_list_table(soup, 'table_v2')
    details['injury_and_suspension'] = parse_injury_suspension(soup)
    details['last_match_lineups'] = parse_last_match_lineups(soup)
    return details
