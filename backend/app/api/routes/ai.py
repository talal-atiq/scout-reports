from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
import httpx
import os
import json
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.dependencies import get_db

load_dotenv()

router = APIRouter(prefix="/ai", tags=["AI Annotations"])

class AiScoutReportRequest(BaseModel):
    player_name: str
    season: str = "25-26"
    
class AiScoutReportResponse(BaseModel):
    executive_summary: str
    pizza_chart_analysis: str
    heatmap_analysis: str
    skill_translation_analysis: str
    expected_threat_analysis: str
    passing_corridors_analysis: str
    positive_development_factors: list[str]
    concerns_and_next_steps: list[str]

@router.post("/scout-report", response_model=AiScoutReportResponse)
async def generate_ai_scout_report(
    req: AiScoutReportRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured on server.")

    # Fetch context data from MongoDB
    collection_name = f"players_stats_{req.season}"
    player_data = await db[collection_name].find_one(
        {"player.name": {"$regex": req.player_name, "$options": "i"}}
    )
    
    spatial_data = await db["player_spatial_profiles"].find_one(
        {"player_name": {"$regex": req.player_name, "$options": "i"}}
    )

    if not player_data and not spatial_data:
        raise HTTPException(status_code=404, detail="Player data not found for AI report.")

    # Assemble context
    context_str = f"Player: {req.player_name}\n"
    if player_data:
        p_info = player_data.get("player", {})
        context_str += f"Age: {p_info.get('age', 'N/A')}\n"
        context_str += f"Position: {p_info.get('position', 'N/A')}\n"
        
        stats = player_data.get("statistics", {})
        context_str += f"Goals: {stats.get('goals', 'N/A')}\n"
        context_str += f"Assists: {stats.get('assists', 'N/A')}\n"
        context_str += f"Pass Accuracy: {stats.get('passes', {}).get('accuracy', 'N/A')}%\n"
        
    if spatial_data:
        context_str += f"Pos Group: {spatial_data.get('pos_group', 'N/A')}\n"
        context_str += f"Percentile Ranks:\n"
        for k, v in spatial_data.get("percentiles_2526", {}).items():
            if isinstance(v, (int, float)):
                context_str += f" - {k}: {v:.1f}%\n"
                
        xt_zones = spatial_data.get("xT_zones")
        if xt_zones and isinstance(xt_zones, dict) and "grid" in xt_zones:
            # Just say that xT data exists and is mapped. The LLM can infer from progressive_actions percentile
            context_str += "Expected Threat (xT) Spatial Matrix: [Matrix Data Present]\n"
            
        pass_vectors = spatial_data.get("pass_vectors")
        if pass_vectors and isinstance(pass_vectors, list):
            context_str += f"Pass Network Matrix: [{len(pass_vectors)} dominant progressive/key pass clusters identified]\n"
            
        touch_heatmap = spatial_data.get("touch_heatmap")
        if touch_heatmap and isinstance(touch_heatmap, dict) and "all" in touch_heatmap:
            context_str += "Pitch Geography Touch Heatmap: [Grid Data Present]\n"

    system_prompt = (
        "You are an elite European Director of Football and Chief Data Scout. Your job is to analyze "
        "the provided raw statistical data, spatial percentiles, and tactical matrices for the given player. "
        "Provide a deeply analytical, professional scouting report without generic filler. Use proper scouting "
        "terminology (e.g., 'progressive carrier', 'half-spaces', 'rest-defense', 'box-crasher').\n\n"
        "Output ONLY a valid JSON object matching the requested schema. Do NOT output markdown code blocks, "
        "just raw parseable JSON.\n\n"
        "Schema:\n"
        "{\n"
        '  "executive_summary": "1-2 sentence high-impact verdict on the player\'s current level and profile.",\n'
        '  "pizza_chart_analysis": "Concise analysis of their statistical footprint. Highlight elite percentiles and concerning drop-offs.",\n'
        '  "heatmap_analysis": "Analyze their pitch geography. Do they hug the touchline? Drop deep? Operate in the half-spaces?",\n'
        '  "skill_translation_analysis": "A scout\'s assessment of how their technical/physical profile translates to other top 5 European leagues.",\n'
        '  "expected_threat_analysis": "Evaluate their progressive actions and expected threat (xT). Are they a primary ball progressor?",\n'
        '  "passing_corridors_analysis": "Assess their passing network. Do they play safe lateral passes or line-breaking verticals?",\n'
        '  "positive_development_factors": ["A list of 4-6 specific sentences highlighting their tactical strengths, translatability, or contextual advantages (e.g. team relegation)."],\n'
        '  "concerns_and_next_steps": ["A list of 3-5 specific sentences highlighting their limitations, weaknesses, or next career steps."]\n'
        "}\n\n"
        "Analyze the player neutrally and professionally. Be highly specific to the numbers provided."
    )

    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the data for {req.player_name}:\n{context_str}"}
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            
            return AiScoutReportResponse(
                executive_summary=parsed.get("executive_summary", "No summary provided."),
                pizza_chart_analysis=parsed.get("pizza_chart_analysis", "No analysis provided."),
                heatmap_analysis=parsed.get("heatmap_analysis", "No analysis provided."),
                skill_translation_analysis=parsed.get("skill_translation_analysis", "No analysis provided."),
                expected_threat_analysis=parsed.get("expected_threat_analysis", "No analysis provided."),
                passing_corridors_analysis=parsed.get("passing_corridors_analysis", "No analysis provided."),
                positive_development_factors=parsed.get("positive_development_factors", []),
                concerns_and_next_steps=parsed.get("concerns_and_next_steps", [])
            )
    except Exception as e:
        print("Groq API Error:", str(e))
        raise HTTPException(status_code=500, detail="Failed to generate AI scout report.")
