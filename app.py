import streamlit as st
import json
import google.generativeai as genai
import re

# =====================================================================
# Aplicación Web: Generador de Entrenadores Moodle (Streamlit)
# Arquitectura: Cliente-Servidor (Serverless / Cloud Deployable)
# =====================================================================

# Configuración inicial de la interfaz de Streamlit
st.set_page_config(page_title="Generador Moodle IA", page_icon="🧠", layout="centered")

# --- PLANTILLA MAESTRA INCRUSTADA ---
# Se incrusta la plantilla HTML/React en el código de servidor. 
# Esto elimina la necesidad de gestionar múltiples archivos estáticos al desplegar en la nube.
PLANTILLA_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITULO_DEL_TEMA}}</title>
    
    <!-- Fuentes y Tailwind CSS -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- React & ReactDOM (Modo Producción recomendado para Moodle) -->
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    
    <!-- Babel (Para compilar JSX en el cliente) -->
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <!-- Marked (Para renderizar markdown del feedback de IA) -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fade-in { animation: fadeIn 0.4s ease-out forwards; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #f1f1f1; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
    </style>
    <script>
        tailwind.config = { theme: { extend: { colors: { teal: { 50: '#f0fdfa', 600: '#0d9488', 700: '#0f766e', 800: '#115e59' } } } } }
    </script>
</head>
<body>
    <div id="root"></div>

    <!-- INYECCIÓN SEGURA DE DATOS (Estándar SSR) -->
    <!-- Esto previene errores de sintaxis en JavaScript si el texto contiene caracteres de escape o backticks -->
    <script id="moodle-data" type="application/json">
        {{JSON_DATA_AQUI}}
    </script>

    <script type="text/babel">
        // ==========================================
        // CONFIGURACIÓN INYECTADA POR PYTHON
        // ==========================================
        const CLAVE_DEL_PROFESOR = "{{API_KEY_AQUI}}"; 
        const APP_TITLE = "{{TITULO_DEL_TEMA}}";
        
        let INITIAL_DATA = [];
        try {
            const dataNode = document.getElementById('moodle-data');
            // Verificamos que Python ha reemplazado el placeholder
            if(dataNode && !dataNode.textContent.includes("JSON_DATA_AQUI")) {
                INITIAL_DATA = JSON.parse(dataNode.textContent);
            }
        } catch(e) {
            console.error("Error crítico de parseo del JSON inyectado.", e);
        }
        // ==========================================

        // Iconos SVG (Optimizados como componentes funcionales estáticos)
        const BrainIcon = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z" /><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z" /></svg>;
        const ActivityIcon = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>;
        const CheckIcon = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><polyline points="20 6 9 17 4 12" /></svg>;
        const XIcon = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>;
        const ChevronRightIcon = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><polyline points="9 18 15 12 9 6" /></svg>;
        const SparklesIcon = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" /></svg>;
        const BotIcon = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M12 8V4H8" /><rect width="16" height="12" x="4" y="8" rx="2" /><path d="M2 14h2" /><path d="M20 14h2" /><path d="M15 13v2" /><path d="M9 13v2" /></svg>;
        const BookOpenIcon = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" /></svg>;
        const RefreshIcon = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" /><path d="M3 3v5h5" /><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" /><path d="M16 21h5v-5" /></svg>;

        // Función centralizada para llamadas a la IA (con reintentos)
        const generateContent = async (prompt) => {
            if (!CLAVE_DEL_PROFESOR || CLAVE_DEL_PROFESOR.includes("API_KEY_AQUI")) return "Modo demostración: Configure su API Key.";
            const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${CLAVE_DEL_PROFESOR}`;
            
            for (let i = 0; i < 5; i++) {
                try {
                    const response = await fetch(url, { 
                        method: 'POST', 
                        headers: { 'Content-Type': 'application/json' }, 
                        body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }) 
                    });
                    if (!response.ok) throw new Error(`API Error: ${response.status}`);
                    const data = await response.json();
                    return data.candidates[0].content.parts[0].text;
                } catch (error) {
                    if (i === 4) return "Error de conexión con el tutor IA. Inténtalo de nuevo.";
                    await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i))); // Exponential backoff
                }
            }
        };

        // --- COMPONENTES DE VISTA ---

        const IntroScreen = ({ onStart }) => (
            <div className="min-h-screen flex items-center justify-center p-4 bg-slate-50 animate-fade-in relative overflow-hidden">
                <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl overflow-hidden relative z-10 border border-slate-200">
                    <div className="bg-teal-700 p-8 md:p-12 text-white relative overflow-hidden">
                        <div className="relative z-10">
                            <span className="inline-block px-3 py-1 bg-teal-800 text-teal-100 text-xs font-bold tracking-wider uppercase rounded-full mb-4">Módulo de Entrenamiento Interactivo</span>
                            <h1 className="text-3xl md:text-4xl font-bold mb-4">{APP_TITLE}</h1>
                        </div>
                    </div>
                    <div className="p-8 md:p-12">
                        <button onClick={onStart} className="w-full bg-teal-600 hover:bg-teal-700 text-white text-lg font-semibold py-4 px-8 rounded-xl shadow-lg flex items-center justify-center gap-3 transition-colors">
                            <span>Comenzar Entrenamiento</span><ChevronRightIcon className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </div>
        );

        const QuizScreen = ({ question, totalQuestions, currentAnswer, setAnswer, onHint, onCompare, loadingHint, hint, onExit }) => (
            <div className="min-h-screen bg-slate-50 flex flex-col items-center p-4 md:p-8 animate-fade-in">
                <div className="w-full max-w-4xl flex justify-between items-center mb-8">
                    <div className="flex items-center gap-2 text-teal-700 font-semibold"><ActivityIcon className="w-5 h-5" /><span>Caso {question.id} de {totalQuestions}</span></div>
                    <button onClick={onExit} className="text-slate-400 hover:text-rose-500 p-1" title="Salir"><XIcon className="w-6 h-6" /></button>
                </div>
                <div className="w-full max-w-4xl bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden">
                    <div className="p-8 md:p-10">
                        <div className="text-sm font-bold text-teal-600 mb-2 uppercase tracking-wide">{question.category}</div>
                        <h2 className="text-2xl font-bold text-slate-800 mb-8 leading-tight">{question.question}</h2>
                        
                        <textarea 
                            className="w-full h-48 p-5 text-lg border-2 border-slate-200 rounded-xl focus:border-teal-500 focus:outline-none resize-none mb-4" 
                            placeholder="Desarrolla tu razonamiento clínico aquí..." 
                            value={currentAnswer} 
                            onChange={(e) => setAnswer(e.target.value)} 
                            autoFocus 
                        />
                        
                        {hint && (
                            <div className="bg-indigo-50 text-indigo-800 p-4 rounded-xl text-sm border border-indigo-100 mb-4 animate-fade-in">
                                <span className="font-bold flex items-center gap-2 mb-1"><SparklesIcon className="w-4 h-4"/> Pista del Tutor Socrático:</span> 
                                <span dangerouslySetInnerHTML={{ __html: marked.parseInline(hint) }} />
                            </div>
                        )}
                        
                        <div className="flex flex-col sm:flex-row gap-4">
                            <button onClick={onHint} disabled={loadingHint || hint} className={`flex-1 py-3 px-6 rounded-xl border-2 font-semibold flex justify-center items-center gap-2 transition-colors ${loadingHint ? 'border-slate-100 text-slate-400 bg-slate-50' : 'border-teal-100 text-teal-700 hover:bg-teal-50'}`}>
                                {loadingHint ? <span className="animate-spin h-4 w-4 border-2 border-slate-400 border-t-transparent rounded-full"></span> : null}
                                {loadingHint ? 'Consultando Tutor...' : 'Pedir Orientación (Método Socrático)'}
                            </button>
                            <button onClick={onCompare} disabled={!currentAnswer.trim()} className={`flex-1 py-3 px-6 rounded-xl font-semibold text-white shadow-md transition-all ${!currentAnswer.trim() ? 'bg-slate-300 cursor-not-allowed' : 'bg-teal-600 hover:bg-teal-700'}`}>
                                Evaluar mi Criterio
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );

        const FeedbackScreen = ({ question, userAnswer, onNext, onEvaluate, loadingEval, aiFeedback }) => {
            return (
                <div className="min-h-screen bg-slate-50 flex flex-col items-center p-4 md:p-8 animate-fade-in pb-24">
                     <div className="w-full max-w-6xl grid md:grid-cols-2 gap-8 flex-grow mb-8">
                        
                        {/* Panel del Alumno */}
                        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2"><BookOpenIcon className="w-4 h-4"/> Tu Razonamiento</h3>
                            <p className="text-slate-800 text-lg whitespace-pre-wrap flex-grow bg-slate-50 p-4 rounded-xl">{userAnswer}</p>
                            
                            <div className="mt-8 pt-6 border-t border-slate-100">
                                {!aiFeedback ? (
                                    <button onClick={onEvaluate} disabled={loadingEval} className="w-full flex items-center justify-center gap-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 py-3 rounded-lg font-medium transition-colors">
                                        {loadingEval ? <span className="animate-spin h-5 w-5 border-2 border-indigo-600 border-t-transparent rounded-full"></span> : <BotIcon className="w-5 h-5" />}
                                        {loadingEval ? 'El IA está analizando tu respuesta...' : 'Pedir Evaluación Formativa a la IA'}
                                    </button>
                                ) : (
                                    <div className="bg-indigo-50 rounded-lg p-4 text-sm text-indigo-900 border border-indigo-100 animate-fade-in">
                                        <div className="font-bold flex items-center gap-2 mb-2 text-indigo-700"><BotIcon className="w-4 h-4"/> Feedback Estructurado:</div>
                                        <div className="prose prose-sm prose-indigo leading-relaxed" dangerouslySetInnerHTML={{ __html: marked.parse(aiFeedback) }} />
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Panel del Gold Standard */}
                        <div className="bg-teal-50 p-6 rounded-2xl border border-teal-100 shadow-sm flex flex-col">
                            <h3 className="text-xs font-bold text-teal-600 uppercase tracking-wider mb-4 flex items-center gap-2"><CheckIcon className="w-4 h-4"/> Estándar Clínico (Gold Standard)</h3>
                            <p className="text-slate-800 text-lg font-medium mb-6 leading-relaxed">{question.idealAnswer}</p>
                            
                            <div className="mt-auto">
                                <h4 className="text-sm font-semibold text-teal-800 mb-3">Conceptos Clave Obligatorios:</h4>
                                <div className="flex flex-wrap gap-2">
                                    {question.keywords.map((kw, i) => (
                                        <span key={i} className="px-3 py-1 bg-white text-teal-800 text-sm font-medium rounded-lg border border-teal-200 shadow-sm">{kw}</span>
                                    ))}
                                </div>
                            </div>
                        </div>
                     </div>
                     
                     {/* Botonera de Auto-evaluación */}
                     <div className="fixed bottom-0 left-0 w-full bg-white border-t border-slate-200 p-4 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-50">
                         <div className="w-full max-w-4xl mx-auto flex gap-4">
                             <button onClick={() => onNext(0)} className="flex-1 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 py-3 rounded-xl font-bold flex justify-center items-center gap-2 transition-colors">
                                <XIcon className="w-5 h-5"/> <span>Debo Repasar Esto</span>
                             </button>
                             <button onClick={() => onNext(1)} className="flex-1 bg-teal-600 hover:bg-teal-700 text-white py-3 rounded-xl font-bold shadow-md flex justify-center items-center gap-2 transition-colors">
                                <CheckIcon className="w-5 h-5"/> <span>Dominado (Seguro)</span>
                             </button>
                         </div>
                     </div>
                </div>
            );
        };

        const ResultsScreen = ({ score, total, onRestart }) => (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 animate-fade-in">
                <div className="max-w-md w-full bg-white rounded-3xl shadow-xl p-8 md:p-12 text-center border border-slate-100">
                    <div className="text-6xl font-bold mb-4 text-teal-600">{Math.round((score/total)*100)}%</div>
                    <h2 className="text-2xl font-bold text-slate-800 mb-8">Nivel de Seguridad Clínica</h2>
                    
                    <div className="bg-slate-50 rounded-xl p-4 mb-8 text-sm text-slate-600 flex justify-between px-8">
                        <div className="text-center"><div className="font-bold text-xl text-slate-800">{score}</div><div>Decisiones Seguras</div></div>
                        <div className="w-px bg-slate-200"></div>
                        <div className="text-center"><div className="font-bold text-xl text-slate-800">{total}</div><div>Casos Totales</div></div>
                    </div>

                    <button onClick={onRestart} className="w-full bg-slate-800 hover:bg-slate-900 text-white font-bold py-4 rounded-xl shadow-lg transition-colors flex items-center justify-center gap-2">
                        <RefreshIcon className="w-5 h-5"/> <span>Reiniciar Guardia</span>
                    </button>
                </div>
            </div>
        );

        // --- COMPONENTE PRINCIPAL (CONTROLADOR ESTADO) ---

        const App = () => {
            const [gameState, setGameState] = React.useState('intro');
            const [currentQIndex, setCurrentQIndex] = React.useState(0);
            const [userAnswer, setUserAnswer] = React.useState('');
            const [score, setScore] = React.useState(0);
            
            // Estado de IA
            const [hint, setHint] = React.useState('');
            const [loadingHint, setLoadingHint] = React.useState(false);
            const [aiFeedback, setAiFeedback] = React.useState('');
            const [loadingEval, setLoadingEval] = React.useState(false);

            if (!INITIAL_DATA || INITIAL_DATA.length === 0) {
                return (
                    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
                        <div className="bg-white p-8 rounded-xl shadow-lg border-l-4 border-rose-500 max-w-md text-center">
                            <h2 className="text-xl font-bold text-rose-600 mb-2">Ausencia de Datos</h2>
                            <p className="text-slate-600">El archivo no contiene viñetas clínicas inyectadas. Este archivo debe ser generado a través de la aplicación de profesorado.</p>
                        </div>
                    </div>
                );
            }

            const handleStart = () => { setGameState('quiz'); setCurrentQIndex(0); setScore(0); resetRound(); };
            const resetRound = () => { setUserAnswer(''); setHint(''); setAiFeedback(''); setLoadingHint(false); setLoadingEval(false); };

            const handleGetHint = async () => {
                setLoadingHint(true);
                const q = INITIAL_DATA[currentQIndex];
                const prompt = `Actúa como tutor socrático para ${q.tutorAudience}. El alumno lee: "${q.question}". Proporciona 1 pista breve o pregunta guía (máximo 2 frases) para encauzar su pensamiento. NO le des la respuesta directa. La respuesta ideal es: ${q.idealAnswer}`;
                setHint(await generateContent(prompt));
                setLoadingHint(false);
            };

            const handleEvaluation = async () => {
                setLoadingEval(true);
                const q = INITIAL_DATA[currentQIndex];
                const prompt = `Evalúa el criterio de un alumno de ${q.tutorAudience}. \nPregunta: "${q.question}". \nRespuesta del alumno: "${userAnswer}". \nRespuesta Ideal Esperada: "${q.idealAnswer}". \nKeywords críticas: ${q.keywords.join(', ')}. \n\nInstrucciones: Devuelve un feedback clínico estricto en formato Markdown (Máximo 80 palabras). \nEstructura obligatoria: \n1. **Evaluación:** (Correcto/Parcial/Peligroso) con justificación en 1 línea. \n2. **Red Flag / Consejo Clínico:** El insight más importante para su nivel.`;
                setAiFeedback(await generateContent(prompt));
                setLoadingEval(false);
            };

            const handleNext = (pts) => {
                setScore(s => s + pts);
                if (currentQIndex < INITIAL_DATA.length - 1) { 
                    setCurrentQIndex(i => i + 1); 
                    resetRound(); 
                    setGameState('quiz'); 
                } else {
                    setGameState('results');
                }
            };

            return (
                <div className="font-sans text-slate-900">
                    {gameState === 'intro' && <IntroScreen onStart={handleStart} />}
                    {gameState === 'quiz' && <QuizScreen question={INITIAL_DATA[currentQIndex]} totalQuestions={INITIAL_DATA.length} currentAnswer={userAnswer} setAnswer={setUserAnswer} onHint={handleGetHint} onCompare={() => setGameState('feedback')} loadingHint={loadingHint} hint={hint} onExit={() => setGameState('intro')} />}
                    {gameState === 'feedback' && <FeedbackScreen question={INITIAL_DATA[currentQIndex]} userAnswer={userAnswer} onNext={handleNext} onEvaluate={handleEvaluation} loadingEval={loadingEval} aiFeedback={aiFeedback} />}
                    {gameState === 'results' && <ResultsScreen score={score} total={INITIAL_DATA.length} onRestart={handleStart} />}
                </div>
            );
        };
        
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>"""

def extraer_json_con_ia(api_key, texto_apuntes):
    """
    Delega a Gemini la tarea probabilística de extraer conocimiento estructurado.
    Implementa limpieza mediante expresiones regulares para garantizar robustez.
    """
    genai.configure(api_key=api_key)
    # Usamos el modelo flash por velocidad y eficiencia en procesamiento de texto estructurado.
    modelo = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Eres un experto estructurador de datos educativos.
    Analiza el texto y devuelve EXCLUSIVAMENTE un objeto JSON válido, sin comentarios ni explicaciones adicionales.
    
    Estructura OBLIGATORIA:
    {{
        "titulo": "Un título representativo e inferido del tema (String)",
        "preguntas": [
            {{ 
                "id": 1, 
                "category": "Categoría clínica o temática (String corto)", 
                "question": "El enunciado del caso o pregunta (String)", 
                "idealAnswer": "La respuesta o resolución teórica completa (String)", 
                "keywords": ["palabra1", "palabra2"], 
                "tutorAudience": "Nivel del alumno objetivo (String, ej: Estudiantes Universitarios)" 
            }}
        ]
    }}
    
    Texto a analizar:
    {texto_apuntes}
    """
    
    response = modelo.generate_content(prompt)
    raw_text = response.text.strip()
    
    # 1. Limpiar bloques markdown (Típico de los LLMs)
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:-3].strip()
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:-3].strip()
        
    # 2. Búsqueda de salvaguarda: si aún hay texto basura, extraer solo la estructura de llaves principal.
    json_match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
    if json_match:
        raw_text = json_match.group(1)
        
    return json.loads(raw_text)

# --- INTERFAZ DE USUARIO (GUI) CON STREAMLIT ---

st.title("🧠 Generador de Entrenadores Moodle")
st.markdown("Convierte tus apuntes teóricos (texto plano) en módulos web interactivos (React/HTML) de *Active Recall*, listos para desplegar en tu plataforma de eLearning.")

# Panel lateral para configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    st.info("La API Key es necesaria tanto para procesar el texto ahora, como para integrarla en el archivo HTML final que usarán los alumnos para consultar al Tutor IA.")
    # Uso type="password" para no exponer la clave visualmente al compartir pantalla
    api_key_input = st.text_input("Ingresa tu Google Gemini API Key", type="password")

st.subheader("Paso 1: Sube el contenido base")
uploaded_file = st.file_uploader("Selecciona un archivo .txt con temario, casos o preguntas", type="txt")

if uploaded_file and api_key_input:
    # Decodificar el archivo asumiendo utf-8
    texto = uploaded_file.getvalue().decode("utf-8")
    
    if st.button("🚀 Crear Entrenador Interactivo", type="primary"):
        with st.spinner("La IA está estructurando el conocimiento (esto puede tardar 10-20 segundos)..."):
            try:
                # 1. Fase de Inteligencia Artificial (Extracción estructurada)
                datos_ia = extraer_json_con_ia(api_key_input, texto)
                
                titulo_tema = datos_ia.get("titulo", "Módulo de Entrenamiento")
                array_preguntas = datos_ia.get("preguntas", [])
                
                if not array_preguntas:
                    st.error("La IA no pudo extraer ninguna pregunta del texto proporcionado.")
                    st.stop()
                
                # 2. Fase de Inyección Determinista (Sustitución en el Servidor)
                # ensure_ascii=False evita que los tildes y caracteres especiales se escapen ilegiblemente.
                json_string_seguro = json.dumps(array_preguntas, ensure_ascii=False)
                
                html_final = PLANTILLA_HTML.replace("{{TITULO_DEL_TEMA}}", titulo_tema)
                html_final = html_final.replace("{{API_KEY_AQUI}}", api_key_input)
                html_final = html_final.replace("{{JSON_DATA_AQUI}}", json_string_seguro)
                
                st.success(f"¡Éxito! Se han estructurado {len(array_preguntas)} casos de estudio correspondientes al tema: **{titulo_tema}**.")
                
                # 3. Fase de Generación de Artefacto
                nombre_archivo = f"entrenador_{titulo_tema.replace(' ', '_').lower()}.html"
                
                st.download_button(
                    label="📥 Descargar archivo HTML (Subir a Moodle)",
                    data=html_final,
                    file_name=nombre_archivo,
                    mime="text/html"
                )
                
                # Opcional: Debug/Validación visual para el profesor
                with st.expander("🔍 Ver estructura JSON extraída por la IA"):
                    st.json(datos_ia)
                    
            except Exception as e:
                st.error(f"Se ha producido un error durante el procesamiento. Verifica el formato del texto o tu API Key. Detalle técnico: {str(e)}")
                
elif not api_key_input:
    st.warning("👈 Por favor, introduce tu API Key en la barra lateral para comenzar.")