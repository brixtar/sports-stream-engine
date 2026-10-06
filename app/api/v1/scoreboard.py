from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from app.core.ws_manager import ws_manager
from app.services.obs_service import obs_service

router = APIRouter(prefix="/scoreboard", tags=["Scoreboard"])

class Player(BaseModel):
    id: str
    number: int
    name: str
    is_starter: bool = True
    position: Optional[str] = "DEL"

class SubstitutionRequest(BaseModel):
    team: str # "local" | "visitante"
    player_out: Player
    player_in: Player
    duration: int = 8

class GoalEvent(BaseModel):
    team: str # "local" | "visitante"
    player_name: Optional[str] = "Jugador"
    player_number: Optional[int] = None
    minute: Optional[str] = "15'"
    duration: int = 7

class CardEvent(BaseModel):
    team: str # "local" | "visitante"
    player: Player
    card_type: str # "yellow" | "red"
    duration: int = 6

class PhaseEvent(BaseModel):
    phase: str # "start_1t", "halftime", "start_2t", "fulltime"

class LineupEvent(BaseModel):
    team: str # "local" | "visitante"
    formation: Optional[str] = "4-3-3"
    coach: Optional[str] = "Director Técnico"
    duration: int = 15

class SoundCueEvent(BaseModel):
    cue_type: str # "whistle_1", "whistle_2", "whistle_3", "buzzer", "horn"

class SummaryEvent(BaseModel):
    duration: int = 20

class ScoreboardState(BaseModel):
    sport: str = "futbol" # "futbol" | "basquet"
    local_name: str = "LOCAL"
    visitante_name: str = "VISITANTE"
    local_logo: Optional[str] = "/uploads/default_local.png"
    visitante_logo: Optional[str] = "/uploads/default_visitante.png"
    local_color: str = "#1e3a8a"
    visitante_color: str = "#991b1b"
    local_score: int = 0
    visitante_score: int = 0
    period: str = "1T"
    timer_seconds: int = 0
    timer_running: bool = False
    timer_mode_90: bool = True
    added_time_minutes: int = 0
    show_added_time: bool = False
    is_match_finished: bool = False
    
    # Penales (Fútbol)
    show_penalties: bool = False
    local_penalties: List[str] = []
    visitante_penalties: List[str] = []
    
    # Básquet específicos
    local_abbrev: Optional[str] = "LOC"
    visitante_abbrev: Optional[str] = "VIS"
    possession: Optional[str] = None # "local" | "visitante" | None
    tournament_title: Optional[str] = "NBA ON ABC"
    local_fouls: int = 0
    visitante_fouls: int = 0
    local_timeouts: int = 5
    visitante_timeouts: int = 5
    shot_clock_seconds: int = 24
    shot_clock_running: bool = False
    
    # Plantillas
    local_players: List[Player] = []
    visitante_players: List[Player] = []

DEFAULT_SPORT = os.getenv("SPORT_DEFAULT", "futbol").lower()
initial_period = "1ST" if DEFAULT_SPORT == "basquet" else "1T"
initial_timer = 600 if DEFAULT_SPORT == "basquet" else 0
initial_lcolor = "#98002E" if DEFAULT_SPORT == "basquet" else "#1e3a8a"
initial_vcolor = "#1D428A" if DEFAULT_SPORT == "basquet" else "#991b1b"
initial_lname = "MIA" if DEFAULT_SPORT == "basquet" else "LOCAL"
initial_vname = "NY" if DEFAULT_SPORT == "basquet" else "VISITANTE"

state = ScoreboardState(
    sport=DEFAULT_SPORT,
    period=initial_period,
    timer_seconds=initial_timer,
    local_name=initial_lname,
    visitante_name=initial_vname,
    local_abbrev=initial_lname[:3].upper(),
    visitante_abbrev=initial_vname[:3].upper(),
    local_color=initial_lcolor,
    visitante_color=initial_vcolor
)

@router.get("/state", response_model=ScoreboardState)
async def get_scoreboard_state():
    return state

@router.post("/update")
async def update_scoreboard(new_state: ScoreboardState):
    global state
    # PRESERVAR EL CRONÓMETRO: Si el reloj está corriendo en el servidor,
    # evitamos que llamadas desde el frontend con estados viejos lo detengan
    if state.timer_running:
        new_state.timer_running = state.timer_running
        new_state.timer_seconds = state.timer_seconds
    if state.shot_clock_running:
        new_state.shot_clock_running = state.shot_clock_running
        new_state.shot_clock_seconds = state.shot_clock_seconds

    state = new_state
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "state": state}

class TeamNamesRequest(BaseModel):
    local_name: Optional[str] = None
    visitante_name: Optional[str] = None
    local_abbrev: Optional[str] = None
    visitante_abbrev: Optional[str] = None
    local_color: Optional[str] = None
    visitante_color: Optional[str] = None
    tournament_title: Optional[str] = None

@router.post("/teams/names")
async def update_team_names(data: TeamNamesRequest):
    """Actualiza nombres, abreviaturas y colores de equipos SIN tocar el cronómetro"""
    global state
    if data.local_name is not None:
        state.local_name = data.local_name
    if data.visitante_name is not None:
        state.visitante_name = data.visitante_name
    if data.local_abbrev is not None:
        state.local_abbrev = data.local_abbrev.upper()
    elif data.local_name is not None:
        state.local_abbrev = data.local_name[:3].upper()

    if data.visitante_abbrev is not None:
        state.visitante_abbrev = data.visitante_abbrev.upper()
    elif data.visitante_name is not None:
        state.visitante_abbrev = data.visitante_name[:3].upper()

    if data.local_color is not None:
        state.local_color = data.local_color
    if data.visitante_color is not None:
        state.visitante_color = data.visitante_color
    if data.tournament_title is not None:
        state.tournament_title = data.tournament_title

    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "state": state}

@router.post("/possession")
async def set_possession(team: Optional[str] = None):
    """Establece la flecha de posesión: 'local', 'visitante', 'toggle' o 'none'"""
    global state
    if team == "toggle":
        state.possession = "visitante" if state.possession == "local" else "local"
    elif team == "none":
        state.possession = None
    elif team in ["local", "visitante"]:
        state.possession = team
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "possession": state.possession}

@router.post("/timer/control")
async def timer_control(action: str, target_seconds: Optional[int] = None):
    global state
    if action == "start":
        state.timer_running = True
        state.is_match_finished = False
        if state.sport == "basquet":
            state.shot_clock_running = True
    elif action == "pause":
        state.timer_running = False
        if state.sport == "basquet":
            state.shot_clock_running = False
    elif action == "toggle":
        state.timer_running = not state.timer_running
        if state.sport == "basquet":
            state.shot_clock_running = state.timer_running
    elif action == "reset_1t":
        state.timer_seconds = 0
        state.timer_running = False
        state.period = "1T"
        state.show_added_time = False
        state.is_match_finished = False
    elif action == "reset_2t":
        state.timer_seconds = 45 * 60 if state.timer_mode_90 else 0
        state.timer_running = False
        state.period = "2T"
        state.show_added_time = False
        state.is_match_finished = False
    elif action in ["quarter_1", "quarter_2", "quarter_3", "quarter_4", "quarter_ot"]:
        q_map = {
            "quarter_1": ("1ST", 600),
            "quarter_2": ("2ND", 600),
            "quarter_3": ("3RD", 600),
            "quarter_4": ("4TH", 600),
            "quarter_ot": ("OT", 300)
        }
        p_name, default_sec = q_map[action]
        state.period = p_name
        state.timer_seconds = target_seconds if target_seconds is not None else default_sec
        state.timer_running = False
        state.shot_clock_seconds = 24
        state.shot_clock_running = False
        state.is_match_finished = False
    elif action == "halftime":
        state.timer_running = False
        if state.sport == "basquet":
            state.period = "HALF"
            state.shot_clock_running = False
        else:
            state.period = "ENTRETIEMPO"
        state.show_added_time = False
    elif action == "fulltime":
        state.timer_running = False
        if state.sport == "basquet":
            state.period = "FINAL"
            state.shot_clock_running = False
        else:
            state.period = "FINAL"
        state.is_match_finished = True
        state.show_added_time = False
    elif action == "set" and target_seconds is not None:
        state.timer_seconds = target_seconds

    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "state": state}

@router.post("/period/set")
async def set_period(period: str):
    """Establece el período o cuarto (1Q, 2Q, 3Q, 4Q, OT, 1ST, etc.)"""
    global state
    state.period = period.upper()
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "period": state.period}

@router.post("/shot_clock/control")
async def shot_clock_control(action: str, delta: Optional[int] = None):
    """Control del reloj de posesión de básquetbol (24s / 14s / toggle / start / stop)"""
    global state
    if action == "reset_24":
        state.shot_clock_seconds = 24
    elif action == "reset_14":
        state.shot_clock_seconds = 14
    elif action == "toggle":
        state.shot_clock_running = not state.shot_clock_running
    elif action == "start":
        state.shot_clock_running = True
    elif action in ["stop", "pause"]:
        state.shot_clock_running = False
    elif action == "delta" and delta is not None:
        state.shot_clock_seconds = max(0, min(99, state.shot_clock_seconds + delta))

    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "shot_clock_seconds": state.shot_clock_seconds, "shot_clock_running": state.shot_clock_running}

@router.post("/timer/adjust")
async def timer_adjust(delta: int):
    """Suma o resta segundos al cronómetro (+60s, -60s, etc.)"""
    global state
    state.timer_seconds = max(0, state.timer_seconds + delta)
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "timer_seconds": state.timer_seconds}

@router.post("/fouls")
async def set_fouls(team: str, delta: int = 0, action: Optional[str] = None):
    """Suma, resta o reinicia faltas de equipo"""
    global state
    if team == "local":
        if action == "reset":
            state.local_fouls = 0
        else:
            state.local_fouls = max(0, state.local_fouls + delta)
    elif team == "visitante":
        if action == "reset":
            state.visitante_fouls = 0
        else:
            state.visitante_fouls = max(0, state.visitante_fouls + delta)
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "local_fouls": state.local_fouls, "visitante_fouls": state.visitante_fouls}

@router.post("/timeouts")
async def set_timeouts(team: str, delta: int = 0, val: Optional[int] = None):
    """Suma, resta o establece tiempos muertos (timeouts)"""
    global state
    if team == "local":
        if val is not None:
            state.local_timeouts = val
        else:
            state.local_timeouts = max(0, min(7, state.local_timeouts + delta))
    elif team == "visitante":
        if val is not None:
            state.visitante_timeouts = val
        else:
            state.visitante_timeouts = max(0, min(7, state.visitante_timeouts + delta))
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "local_timeouts": state.local_timeouts, "visitante_timeouts": state.visitante_timeouts}


@router.post("/phase/whistle")
async def trigger_phase_whistle(event: PhaseEvent):
    """Dispara animación de fase con sonido de silbato del árbitro en OBS"""
    global state
    if event.phase == "start_1t":
        state.period = "1T"
        state.timer_seconds = 0
        state.timer_running = True
        state.is_match_finished = False
        state.show_added_time = False
    elif event.phase == "halftime":
        state.period = "ENTRETIEMPO"
        state.timer_running = False
        state.show_added_time = False
    elif event.phase == "start_2t":
        state.period = "2T"
        state.timer_seconds = 45 * 60 if state.timer_mode_90 else 0
        state.timer_running = True
        state.show_added_time = False
    elif event.phase == "fulltime":
        state.period = "FINAL"
        state.timer_running = False
        state.is_match_finished = True
        state.show_added_time = False

    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    await ws_manager.broadcast("play_whistle_animation", {
        "phase": event.phase,
        "period": state.period,
        "local_name": state.local_name,
        "visitante_name": state.visitante_name,
        "local_score": state.local_score,
        "visitante_score": state.visitante_score
    })
    return {"status": "ok", "phase": event.phase}

@router.post("/goal/trigger")
async def trigger_goal(goal: GoalEvent):
    """Suma el gol y dispara la animación de ¡GOOOL! con escudo y autor"""
    global state
    if goal.team == "local":
        state.local_score += 1
    else:
        state.visitante_score += 1

    team_name = state.local_name if goal.team == "local" else state.visitante_name
    team_logo = state.local_logo if goal.team == "local" else state.visitante_logo

    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    await ws_manager.broadcast("show_goal_animation", {
        "team": goal.team,
        "team_name": team_name,
        "team_logo": team_logo,
        "player_name": goal.player_name,
        "player_number": goal.player_number,
        "minute": goal.minute,
        "local_score": state.local_score,
        "visitante_score": state.visitante_score,
        "duration": goal.duration
    })
    return {"status": "ok", "state": state}

@router.post("/card/trigger")
async def trigger_card(card: CardEvent):
    """Dispara el zócalo de Tarjeta Amarilla o Roja en OBS"""
    team_name = state.local_name if card.team == "local" else state.visitante_name
    team_logo = state.local_logo if card.team == "local" else state.visitante_logo

    await ws_manager.broadcast("show_card_overlay", {
        "team_name": team_name,
        "team_logo": team_logo,
        "player": card.player.model_dump(),
        "card_type": card.card_type,
        "duration": card.duration
    })
    return {"status": "ok"}

@router.post("/added_time")
async def set_added_time(minutes: int):
    global state
    state.added_time_minutes = minutes
    state.show_added_time = (minutes > 0)
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "state": state}

@router.post("/score")
async def set_score(team: str, delta: int):
    global state
    if team == "local":
        state.local_score = max(0, state.local_score + delta)
    elif team == "visitante":
        state.visitante_score = max(0, state.visitante_score + delta)
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "state": state}

@router.post("/score/reset")
async def reset_score():
    global state
    state.local_score = 0
    state.visitante_score = 0
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "state": state}

@router.post("/penalties/action")
async def penalty_action(team: str, result: str):
    global state
    target_list = state.local_penalties if team == "local" else state.visitante_penalties
    if result == "undo":
        if target_list: target_list.pop()
    elif result in ["scored", "missed"]:
        state.show_penalties = True
        state.period = "PENALES"
        if len(target_list) < 10: target_list.append(result)
    elif result == "reset":
        state.local_penalties = []
        state.visitante_penalties = []
    elif result == "hide":
        state.show_penalties = False
    elif result == "show":
        state.show_penalties = True
    elif result == "toggle":
        state.show_penalties = not state.show_penalties
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "state": state}

@router.post("/substitution/trigger")
async def trigger_substitution(sub: SubstitutionRequest):
    team_logo = state.local_logo if sub.team == "local" else state.visitante_logo
    team_name = state.local_name if sub.team == "local" else state.visitante_name
    payload = {
        "team_name": team_name,
        "team_logo": team_logo,
        "player_out": sub.player_out.model_dump(),
        "player_in": sub.player_in.model_dump(),
        "duration": sub.duration
    }
    await ws_manager.broadcast("show_substitution_overlay", payload)
    return {"status": "ok", "payload": payload}

@router.post("/fouls")
async def set_fouls(team: str, delta: int = 0, set_zero: bool = False):
    global state
    if team == "local":
        state.local_fouls = 0 if set_zero else max(0, state.local_fouls + delta)
    elif team == "visitante":
        state.visitante_fouls = 0 if set_zero else max(0, state.visitante_fouls + delta)
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "state": state}

@router.post("/timeouts")
async def set_timeouts(team: str, delta: int):
    global state
    if team == "local":
        state.local_timeouts = max(0, state.local_timeouts + delta)
    elif team == "visitante":
        state.visitante_timeouts = max(0, state.visitante_timeouts + delta)
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "state": state}

@router.post("/shot_clock/control")
async def shot_clock_control(action: str, target_seconds: Optional[int] = None, delta: Optional[int] = None):
    """Control del reloj de posesión (Shot Clock) de básquetbol (24s / 14s / Start / Pause / Reset)"""
    global state
    if action == "reset_24":
        state.shot_clock_seconds = 24
        state.shot_clock_running = True
    elif action == "reset_14":
        state.shot_clock_seconds = 14
        state.shot_clock_running = True
    elif action == "start":
        state.shot_clock_running = True
    elif action == "pause":
        state.shot_clock_running = False
    elif action == "toggle":
        state.shot_clock_running = not state.shot_clock_running
    elif action == "set" and target_seconds is not None:
        state.shot_clock_seconds = max(0, min(99, target_seconds))
    elif action == "delta" and delta is not None:
        state.shot_clock_seconds = max(0, min(99, state.shot_clock_seconds + delta))
    elif action == "buzzer":
        await ws_manager.broadcast("play_sound_cue", {"cue_type": "buzzer"})

    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "shot_clock_seconds": state.shot_clock_seconds, "shot_clock_running": state.shot_clock_running}

@router.post("/period/set")
async def set_period(period: str):
    global state
    state.period = period
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "period": period}

@router.post("/sport/select")
async def select_sport(sport: str):
    global state
    state.sport = sport
    if sport == "basquet":
        state.period = "1ST"
        state.timer_seconds = 600
        state.shot_clock_seconds = 24
        state.timer_running = False
        state.shot_clock_running = False
    else:
        state.period = "1T"
        state.timer_seconds = 0
        state.timer_running = False

    # Conmutar perfil y colección en OBS Studio
    profile_name = "Futbol" if sport == "futbol" else "Basquetbol"
    obs_service.set_profile(profile_name)
    obs_service.set_scene_collection(profile_name)

    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "sport": sport, "obs_profile": profile_name}

@router.post("/colors")
async def set_colors(local_color: Optional[str] = None, visitante_color: Optional[str] = None):
    """Actualiza los colores primarios de los equipos en el marcador"""
    global state
    if local_color:
        state.local_color = local_color
    if visitante_color:
        state.visitante_color = visitante_color
    await ws_manager.broadcast("scoreboard_updated", state.model_dump())
    return {"status": "ok", "local_color": state.local_color, "visitante_color": state.visitante_color}

@router.post("/lineup/trigger")
async def trigger_lineup(event: LineupEvent):
    """Dispara la placa televisiva de formación / alineación en pantalla"""
    team_name = state.local_name if event.team == "local" else state.visitante_name
    team_logo = state.local_logo if event.team == "local" else state.visitante_logo
    team_color = state.local_color if event.team == "local" else state.visitante_color
    players = state.local_players if event.team == "local" else state.visitante_players

    starters = [p.model_dump() for p in players if p.is_starter]
    subs = [p.model_dump() for p in players if not p.is_starter]

    payload = {
        "team": event.team,
        "team_name": team_name,
        "team_logo": team_logo,
        "team_color": team_color,
        "formation": event.formation or "4-3-3",
        "coach": event.coach or "Director Técnico",
        "starters": starters,
        "subs": subs,
        "duration": event.duration
    }
    await ws_manager.broadcast("show_lineup_overlay", payload)
    return {"status": "ok", "payload": payload}

@router.post("/lineup/hide")
async def hide_lineup():
    """Oculta manualmente la placa de alineación"""
    await ws_manager.broadcast("hide_lineup_overlay", {})
    return {"status": "ok"}

@router.post("/sound/trigger")
async def trigger_sound_cue(event: SoundCueEvent):
    """Dispara un efecto de sonido sintetizado en el audio del stream (OBS Browser Source)"""
    await ws_manager.broadcast("play_sound_cue", {"cue_type": event.cue_type})
    return {"status": "ok", "cue_type": event.cue_type}

@router.post("/summary/trigger")
async def trigger_summary(event: SummaryEvent):
    """Dispara la placa de resumen final del partido para cierre y redes sociales"""
    payload = {
        "local_name": state.local_name,
        "visitante_name": state.visitante_name,
        "local_logo": state.local_logo,
        "visitante_logo": state.visitante_logo,
        "local_color": state.local_color,
        "visitante_color": state.visitante_color,
        "local_score": state.local_score,
        "visitante_score": state.visitante_score,
        "period": state.period,
        "sport": state.sport,
        "duration": event.duration
    }
    await ws_manager.broadcast("show_summary_overlay", payload)
    return {"status": "ok", "payload": payload}

@router.post("/summary/hide")
async def hide_summary():
    """Oculta la placa de resumen final"""
    await ws_manager.broadcast("hide_summary_overlay", {})
    return {"status": "ok"}


