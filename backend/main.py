import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import rdflib

app = FastAPI(
    title="Motion Ontology Backend",
    description="Serviço de retaguarda semântica para o tracker Motion utilizando SPARQL e RDFLib.",
    version="1.0.0"
)

# Configuração de CORS para permitir acesso do app Vue (Vite na porta 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa o Grafo RDF
g = rdflib.Graph()

# Determina caminhos dos arquivos da ontologia
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ontology_files = [
    os.path.join(BASE_DIR, "src", "data", "motion_ontology.ttl"),
    os.path.join(BASE_DIR, "src", "data", "mymotion_ontology.ttl")
]

# Tenta carregar os arquivos de ontologia
loaded_files = []
for filepath in ontology_files:
    if os.path.exists(filepath):
        try:
            g.parse(filepath, format="turtle")
            loaded_files.append(os.path.basename(filepath))
            print(f"Sucesso ao carregar a ontologia: {filepath}")
        except Exception as e:
            print(f"Erro ao analisar o arquivo {filepath}: {e}")
    else:
        print(f"Arquivo não encontrado: {filepath}")

# Mapeamento estático auxiliar de padrões de movimento (Push/Pull/Legs/Core/Cardio) em português
PATTERN_MAPPING = {
    "Flexão Inclinada": "Empurrar",
    "Flexão": "Empurrar",
    "Dips": "Empurrar",
    "Muscle Up": "Misto (Empurrar e Puxar)",
    "Barra Australiana": "Puxar",
    "Barra (Pendurado)": "Puxar",
    "Barra Fixa": "Puxar",
    "Suporte nas Argolas": "Empurrar",
    "Front Lever": "Puxar",
    "Planche": "Empurrar",
    "Agachamento (Squat)": "Pernas",
    "Bulgarian Split Squat": "Pernas",
    "Pistol Squat": "Pernas",
    "Nordic Curl": "Pernas",
    "Prancha": "Core",
    "Hollow Body": "Core",
    "Abdominal Infra": "Core",
    "L-Sit": "Core",
    "Dragon Flag": "Core",
    "Polichinelo": "Cardio",
    "Montanha Alpinista": "Cardio",
    "Burpee": "Cardio"
}

def clean_uri_fragment(uri: rdflib.URIRef) -> str:
    return str(uri).split('#')[-1].split('/')[-1]

def get_exercise_details_dict() -> Dict[str, Dict[str, Any]]:
    """Consulta a ontologia usando SPARQL para obter todos os exercícios e propriedades."""
    query = """
    PREFIX motion: <http://arielcampelo.org/ontologies/motion#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?exercise ?name ?desc ?suggestion ?unit ?levelLabel ?areaLabel ?typeLabel WHERE {
        ?exercise a motion:Exercise ;
                  motion:exerciseName ?name ;
                  motion:description ?desc ;
                  motion:hasLevel ?level ;
                  motion:hasTargetArea ?area ;
                  motion:hasType ?type .
        ?level rdfs:label ?levelLabel .
        ?area rdfs:label ?areaLabel .
        ?type rdfs:label ?typeLabel .
        OPTIONAL { ?exercise motion:suggestion ?suggestion }
        OPTIONAL { ?exercise motion:unit ?unit }
    }
    """
    
    try:
        results = g.query(query)
    except Exception as e:
        print(f"Erro ao executar SPARQL query: {e}")
        return {}

    exercises = {}
    for row in results:
        exercise_uri = row.exercise
        name = str(row.name)
        
        # Consulta os pré-requisitos para este exercício
        req_query = f"""
        PREFIX motion: <http://arielcampelo.org/ontologies/motion#>
        SELECT ?reqName WHERE {{
            <{str(exercise_uri)}> motion:requires ?req .
            ?req motion:exerciseName ?reqName .
        }}
        """
        req_results = g.query(req_query)
        requirements = [str(r.reqName) for r in req_results]
        
        pattern = PATTERN_MAPPING.get(name, "Geral")
        
        exercises[name] = {
            "id": clean_uri_fragment(exercise_uri),
            "name": name,
            "uri": str(exercise_uri),
            "description": str(row.desc),
            "suggestion": str(row.suggestion) if row.suggestion else "",
            "unit": str(row.unit) if row.unit else "reps",
            "level": str(row.levelLabel),
            "area": str(row.areaLabel),
            "type": "isometric" if str(row.typeLabel) == "Isométrico" else "dynamic",
            "pattern": pattern,
            "requirements": requirements
        }
    return exercises

# Pydantic models para request/response
class WorkoutExercise(BaseModel):
    name: str
    sets: int
    reps: int
    area: str

class WorkoutAnalysisRequest(BaseModel):
    exercises: List[WorkoutExercise]

class BlockItem(BaseModel):
    name: str
    reps: Any
    setNumber: Optional[int] = 1
    totalSets: Optional[int] = 1

class WorkoutDetails(BaseModel):
    totalSets: Optional[int] = 0
    totalReps: Optional[int] = 0
    blocks: Optional[List[BlockItem]] = []

class WorkoutHistoryItem(BaseModel):
    name: str
    modalityId: str
    details: Optional[WorkoutDetails] = None

class UserEvaluationRequest(BaseModel):
    history: List[WorkoutHistoryItem]

class AreaLevel(BaseModel):
    level: str
    completed_count: int
    unlocked_next: List[str]

class ExerciseProgress(BaseModel):
    exercise: str
    max_reps_completed: int
    recommended_next_reps: int
    recommended_next_sets: int
    progression_status: str
    next_exercise_suggestion: Optional[str] = None

class UserEvaluationResponse(BaseModel):
    area_levels: Dict[str, AreaLevel]
    exercise_progressions: Dict[str, ExerciseProgress]

@app.get("/")
def read_root():
    return {
        "status": "online",
        "loaded_files": loaded_files,
        "total_triples": len(g)
    }

@app.get("/api/exercises")
def get_exercises():
    """Retorna todos os exercícios definidos na ontologia com dados semânticos."""
    exs = get_exercise_details_dict()
    if not exs:
        raise HTTPException(status_code=500, detail="Erro ao carregar ou consultar exercícios da ontologia.")
    return exs

@app.get("/api/progression-tree")
def get_progression_tree():
    """Gera a árvore de progressão e dependências entre os exercícios."""
    exs = get_exercise_details_dict()
    
    # Monta os nós
    nodes = []
    for name, details in exs.items():
        nodes.append({
            "id": details["name"],
            "name": details["name"],
            "level": details["level"],
            "area": details["area"],
            "pattern": details["pattern"],
            "type": details["type"]
        })
        
    # Consulta as arestas (edges)
    query_edges = """
    PREFIX motion: <http://arielcampelo.org/ontologies/motion#>
    SELECT ?sourceName ?targetName WHERE {
        ?target motion:requires ?source .
        ?source motion:exerciseName ?sourceName .
        ?target motion:exerciseName ?targetName .
    }
    """
    
    edges = []
    try:
        results = g.query(query_edges)
        for row in results:
            edges.append({
                "source": str(row.sourceName),
                "target": str(row.targetName)
            })
    except Exception as e:
        print(f"Erro ao buscar arestas: {e}")
        
    return {
        "nodes": nodes,
        "edges": edges
    }

@app.post("/api/analyze-workout")
def analyze_workout(data: WorkoutAnalysisRequest):
    """Analisa semanticamente a sessão de treino recebida."""
    ontology_exercises = get_exercise_details_dict()
    
    workout_names = [ex.name for ex in data.exercises]
    
    # 1. Contagem de padrões e áreas
    patterns = {"Empurrar": 0, "Puxar": 0, "Pernas": 0, "Core": 0, "Cardio": 0, "Misto (Empurrar e Puxar)": 0, "Geral": 0}
    levels = {"Iniciante": 0, "Intermediário": 0, "Avançado": 0}
    types = {"isometric": 0, "dynamic": 0}
    
    missing_requirements = []
    warnings = []
    recommendations = []
    
    for ex in data.exercises:
        ont_info = ontology_exercises.get(ex.name)
        if ont_info:
            # Padrões
            p = ont_info["pattern"]
            patterns[p] = patterns.get(p, 0) + 1
            if p == "Misto (Empurrar e Puxar)":
                patterns["Empurrar"] += 1
                patterns["Puxar"] += 1
                
            # Níveis
            lvl = ont_info["level"]
            levels[lvl] = levels.get(lvl, 0) + 1
            
            # Tipos (Isométrico vs Dinâmico)
            t = ont_info["type"]
            types[t] = types.get(t, 0) + 1
            
            # Pré-requisitos
            for req in ont_info["requirements"]:
                if req not in workout_names:
                    missing_requirements.append({
                        "exercise": ex.name,
                        "missing": req
                    })
        else:
            # Caso o exercício não esteja na ontologia
            p = PATTERN_MAPPING.get(ex.name, "Geral")
            patterns[p] = patterns.get(p, 0) + 1

    # 2. Avaliação de Equilíbrio Muscular (Push vs Pull)
    push_count = patterns["Empurrar"]
    pull_count = patterns["Puxar"]
    
    if push_count > 0 or pull_count > 0:
        total_upper = push_count + pull_count
        if total_upper > 2:
            push_ratio = push_count / total_upper
            if push_ratio > 0.7:
                warnings.append(
                    "Desequilíbrio de Empurrar: Seu treino tem muitas flexões/paralelas e poucos exercícios de puxar. "
                    "Isso pode causar desequilíbrio e postura cifótica (ombros caídos)."
                )
                recommendations.append("Dica: Adicione exercícios de puxada como Barra Fixa ou Barra Australiana.")
            elif push_ratio < 0.3:
                warnings.append(
                    "Desequilíbrio de Puxar: Seu treino está focado quase inteiramente em puxar. "
                    "Considere equilibrar com exercícios de empurrar para fortalecer o peito e tríceps."
                )
                recommendations.append("Dica: Adicione exercícios como Flexão ou Dips.")

    # 3. Avaliação de Requisitos
    if missing_requirements:
        for item in missing_requirements:
            warnings.append(
                f"Requisito Ausente: O exercício '{item['exercise']}' requer proficiência prévia em '{item['missing']}', "
                f"que não está no seu treino atual."
            )
            # Acha sugestão do requisito na ontologia
            req_info = ontology_exercises.get(item['missing'])
            sug_text = f" Dica: {req_info['suggestion']}" if req_info and req_info['suggestion'] else ""
            recommendations.append(f"Considere adicionar '{item['missing']}' para aquecimento ou progressão gradual.{sug_text}")

    # 4. Avaliação de Dificuldade
    if levels["Avançado"] > 0 and levels["Iniciante"] == 0 and levels["Intermediário"] == 0:
        # Treino puramente avançado é aceitável para atletas, mas avisa sobre aquecimento
        recommendations.append("Seu treino é composto apenas de exercícios Avançados. Certifique-se de realizar um aquecimento geral rigoroso.")
    elif levels["Avançado"] > 0 and (levels["Iniciante"] > 0 or levels["Intermediário"] > 0):
        # Misto
        pass

    # Resumo
    return {
        "patterns": {k: v for k, v in patterns.items() if v > 0},
        "levels": {k: v for k, v in levels.items() if v > 0},
        "types": types,
        "warnings": warnings,
        "recommendations": recommendations,
        "balanced": len(warnings) == 0
    }

@app.post("/api/suggest-next")
def suggest_next(completed_exercises: List[str]):
    """Sugere novos exercícios com base no histórico de exercícios dominados/concluídos."""
    ontology_exercises = get_exercise_details_dict()
    
    completed_set = set(completed_exercises)
    suggestions = []
    
    for name, details in ontology_exercises.items():
        if name in completed_set:
            continue
            
        # Verifica se todos os pré-requisitos estão no histórico (concluídos)
        reqs = details["requirements"]
        if reqs and all(r in completed_set for r in reqs):
            suggestions.append({
                "name": name,
                "reason": f"Você completou todos os pré-requisitos: {', '.join(reqs)}.",
                "details": details
            })
            
    # Se o histórico for vazio, sugere iniciantes
    if not completed_exercises:
        for name, details in ontology_exercises.items():
            if details["level"].lower() == "iniciante" and not details["requirements"]:
                suggestions.append({
                    "name": name,
                    "reason": "Exercício de nível iniciante recomendado para começar.",
                    "details": details
                })
                
    return suggestions[:5] # Retorna no máximo 5 sugestões

@app.post("/api/evaluate-user", response_model=UserEvaluationResponse)
def evaluate_user(data: UserEvaluationRequest):
    ontology_exercises = get_exercise_details_dict()
    
    # 1. Agrupar dados históricos por exercício
    # Encontra o maior número de repetições/segundos por exercício
    # e a estrutura padrão de séries
    exercise_history = {} # name -> {"max_reps": int, "max_sets": int}
    
    for workout in data.history:
        if workout.modalityId != 'calistenia' or not workout.details:
            continue
        
        # Mapeia conjuntos por exercício nesta sessão para contar séries
        session_exercises = {}
        for block in workout.details.blocks:
            name = block.name
            try:
                reps = int(block.reps)
            except:
                reps = 0
            if name not in session_exercises:
                session_exercises[name] = []
            session_exercises[name].append(reps)
            
        for name, reps_list in session_exercises.items():
            if name not in exercise_history:
                exercise_history[name] = {"max_reps": 0, "max_sets": 0}
            max_r = max(reps_list) if reps_list else 0
            sets_count = len(reps_list)
            if max_r > exercise_history[name]["max_reps"]:
                exercise_history[name]["max_reps"] = max_r
            if sets_count > exercise_history[name]["max_sets"]:
                exercise_history[name]["max_sets"] = sets_count

    # 2. Avaliar nível por área alvo (Superior, Core, Inferior, Cardio)
    area_max_difficulty = {
        "Superior": "Iniciante",
        "Core": "Iniciante",
        "Inferior": "Iniciante",
        "Cardio": "Iniciante"
    }
    area_completed_count = {
        "Superior": 0,
        "Core": 0,
        "Inferior": 0,
        "Cardio": 0
    }
    
    difficulty_order = {"Iniciante": 1, "Intermediário": 2, "Avançado": 3}
    completed_names = set(exercise_history.keys())
    
    for name in completed_names:
        ont_info = ontology_exercises.get(name)
        if ont_info:
            area = ont_info["area"]
            lvl = ont_info["level"]
            area_completed_count[area] = area_completed_count.get(area, 0) + 1
            
            # Se o nível deste exercício for maior que o atual da área, atualiza
            current_lvl = area_max_difficulty.get(area, "Iniciante")
            if difficulty_order.get(lvl, 1) > difficulty_order.get(current_lvl, 1):
                area_max_difficulty[area] = lvl

    # 3. Determinar próximos exercícios desbloqueados por área
    # Exercício está desbloqueado se não foi concluído ainda E todos os pré-requisitos foram concluídos
    area_unlocked_next = {
        "Superior": [],
        "Core": [],
        "Inferior": [],
        "Cardio": []
    }
    
    for name, details in ontology_exercises.items():
        if name in completed_names:
            continue
        reqs = details["requirements"]
        if not reqs or all(r in completed_names for r in reqs):
            area = details["area"]
            area_unlocked_next[area].append(name)

    # 4. Calcular progressão de carga e sugestão de avanço
    exercise_progressions = {}
    for name, details in ontology_exercises.items():
        # Se o usuário já executou este exercício
        if name in exercise_history:
            hist = exercise_history[name]
            max_reps = hist["max_reps"]
            max_sets = hist["max_sets"] if hist["max_sets"] > 0 else 3
            
            unit = details["unit"]
            is_isometric = unit == "seconds"
            
            # Limites para sugerir progressão de exercício
            threshold = 30 if is_isometric else 12
            
            progression_status = "progredir_carga"
            next_suggestion = None
            
            # Se atingiu o limite de repetições/segundos, tenta sugerir a próxima progressão
            if max_reps >= threshold:
                # Acha se existe algum exercício na ontologia que requer este exercício
                next_variations = []
                for ex_name, ex_details in ontology_exercises.items():
                    if name in ex_details["requirements"]:
                        next_variations.append(ex_name)
                
                if next_variations:
                    progression_status = "progredir_exercicio"
                    next_suggestion = next_variations[0]
                else:
                    progression_status = "manter"
            
            # Calcula nova carga recomendada
            if progression_status == "progredir_carga":
                recommended_reps = max_reps + (5 if is_isometric else 1)
                recommended_sets = max_sets
            elif progression_status == "progredir_exercicio":
                recommended_reps = max_reps
                recommended_sets = max_sets
            else: # manter
                recommended_reps = max_reps
                recommended_sets = max_sets
                
            exercise_progressions[name] = {
                "exercise": name,
                "max_reps_completed": max_reps,
                "recommended_next_reps": recommended_reps,
                "recommended_next_sets": recommended_sets,
                "progression_status": progression_status,
                "next_exercise_suggestion": next_suggestion
            }
        else:
            unit = details["unit"]
            is_isometric = unit == "seconds"
            exercise_progressions[name] = {
                "exercise": name,
                "max_reps_completed": 0,
                "recommended_next_reps": 30 if is_isometric else 10,
                "recommended_next_sets": 3,
                "progression_status": "manter",
                "next_exercise_suggestion": None
            }

    # Monta a resposta
    area_levels_resp = {}
    for area in area_max_difficulty:
        area_levels_resp[area] = {
            "level": area_max_difficulty[area],
            "completed_count": area_completed_count[area],
            "unlocked_next": area_unlocked_next[area]
        }
        
    return {
        "area_levels": area_levels_resp,
        "exercise_progressions": exercise_progressions
    }

@app.get("/api/training-plans")
def get_training_plans():
    # Consulta SPARQL para recuperar planos, marcos e sessões
    query = """
    PREFIX motion: <http://arielcampelo.org/ontologies/motion#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?plan ?planLabel ?planComment ?milestone ?milestoneLabel ?milestoneOrder ?session ?sessionLabel ?sessionType ?week ?exerciseName ?progression
    WHERE {
        ?plan a motion:TrainingPlan .
        OPTIONAL { ?plan rdfs:label ?planLabel } .
        OPTIONAL { ?plan rdfs:comment ?planComment } .
        
        ?plan motion:hasMilestone ?milestone .
        OPTIONAL { ?milestone rdfs:label ?milestoneLabel } .
        OPTIONAL { ?milestone motion:milestoneOrder ?milestoneOrder } .
        
        ?milestone motion:hasSession ?session .
        OPTIONAL { ?session rdfs:label ?sessionLabel } .
        ?session a ?sessionType .
        FILTER(?sessionType IN (motion:StrengthSession, motion:TechniqueSession)) .
        
        OPTIONAL { ?session motion:stageWeek ?week } .
        OPTIONAL { ?session motion:focusesOnExercise ?exercise .
                   ?exercise motion:exerciseName ?exerciseName } .
        OPTIONAL { ?session motion:suggestedProgression ?progression } .
    }
    """
    
    try:
        results = g.query(query)
        plans = {}
        
        for row in results:
            plan_uri = str(row.plan)
            plan_label = str(row.planLabel) if row.planLabel else "Plano de Treino"
            plan_desc = str(row.planComment) if row.planComment else ""
            
            if plan_uri not in plans:
                plans[plan_uri] = {
                    "id": plan_uri.split("#")[-1],
                    "name": plan_label,
                    "description": plan_desc,
                    "milestones": {}
                }
                
            ms_uri = str(row.milestone)
            ms_label = str(row.milestoneLabel) if row.milestoneLabel else "Marco"
            ms_order = int(row.milestoneOrder) if row.milestoneOrder else 1
            
            if ms_uri not in plans[plan_uri]["milestones"]:
                plans[plan_uri]["milestones"][ms_uri] = {
                    "id": ms_uri.split("#")[-1],
                    "name": ms_label,
                    "order": ms_order,
                    "sessions": []
                }
                
            session_uri = str(row.session)
            session_label = str(row.sessionLabel) if row.sessionLabel else "Sessão"
            session_type = "Força" if "Strength" in str(row.sessionType) else "Técnica"
            week = int(row.week) if row.week else 1
            exercise = str(row.exerciseName) if row.exerciseName else ""
            progression = str(row.progression) if row.progression else ""
            
            plans[plan_uri]["milestones"][ms_uri]["sessions"].append({
                "id": session_uri.split("#")[-1],
                "name": session_label,
                "type": session_type,
                "week": week,
                "exercise": exercise,
                "progression": progression
            })
            
        # Converte dicionário para lista ordenada
        resp = []
        for p_uri, p_data in plans.items():
            ms_list = list(p_data["milestones"].values())
            ms_list.sort(key=lambda x: x["order"])
            
            for ms in ms_list:
                ms["sessions"].sort(key=lambda x: (x["week"], x["type"]))
                
            resp.append({
                "id": p_data["id"],
                "name": p_data["name"],
                "description": p_data["description"],
                "milestones": ms_list
            })
            
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter planos: {str(e)}")
