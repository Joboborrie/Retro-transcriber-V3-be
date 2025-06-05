from flask import Blueprint, request, jsonify
import os
import tempfile
import openai
import re
from datetime import datetime

transcription_bp = Blueprint('transcription', __name__)

# Configure OpenAI (in production, use environment variables)
# openai.api_key = os.getenv('OPENAI_API_KEY', 'your-api-key-here')

@transcription_bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcribe audio file and detect up-sots (key moments)
    """
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            audio_file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # For demo purposes, simulate transcription
            # In production, uncomment the OpenAI Whisper API call below
            
            # with open(temp_file_path, 'rb') as audio:
            #     transcript = openai.Audio.transcribe("whisper-1", audio)
            #     transcription_text = transcript['text']
            
            # Demo transcription text
            transcription_text = """
            Welcome to today's interview. I'm here with John Smith, CEO of TechCorp, to discuss the company's innovative approach to artificial intelligence and machine learning. 

            John, thank you for joining us today. Can you tell us about your background and how you got started in the tech industry?

            Well, thank you for having me. I've been in the technology sector for over fifteen years now. I started as a software engineer right out of college, working on database systems. What really drew me to AI was seeing how machine learning could transform the way we process and understand data.

            That's fascinating. Your company has been making headlines recently with your new AI platform. Can you walk us through what makes it unique?

            Absolutely. Our platform focuses on three key areas: natural language processing, computer vision, and predictive analytics. What sets us apart is our emphasis on ethical AI development and transparency. We believe that AI should be accessible and understandable to everyone, not just technical experts.

            Speaking of ethics, there's been a lot of discussion about responsible AI development. How does TechCorp approach this challenge?

            Ethics is at the core of everything we do. We have a dedicated ethics board that reviews all our AI projects. We also prioritize data privacy and ensure that our algorithms are free from bias. It's not just about building powerful AI; it's about building AI that serves humanity in a positive way.

            Looking ahead, what do you see as the biggest opportunities and challenges in the AI space?

            The opportunities are enormous. AI has the potential to solve some of our most pressing global challenges, from climate change to healthcare. However, we also face significant challenges around regulation, public trust, and ensuring that the benefits of AI are distributed equitably across society.

            That's a great perspective. Before we wrap up, what advice would you give to young entrepreneurs looking to enter the AI space?

            My advice would be to focus on solving real problems. Don't build AI for the sake of AI. Identify genuine pain points and think about how AI can provide meaningful solutions. Also, never underestimate the importance of building a strong, diverse team.

            John, thank you so much for your time and insights today. This has been incredibly valuable.

            Thank you for having me. It's been a pleasure.
            """
            
            # Detect up-sots (key moments) using keyword analysis
            up_sots = detect_up_sots(transcription_text)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return jsonify({
                'success': True,
                'transcription': transcription_text.strip(),
                'up_sots': up_sots,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise e
            
    except Exception as e:
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500

def detect_up_sots(text):
    """
    Detect key moments (up-sots) in the transcription text
    """
    up_sots = []
    
    # Split text into sentences for analysis
    sentences = re.split(r'[.!?]+', text)
    current_time = 0
    
    # Keywords that indicate important moments
    key_phrases = [
        'thank you', 'welcome', 'fascinating', 'absolutely', 'unique',
        'challenge', 'opportunity', 'important', 'key', 'significant',
        'advice', 'perspective', 'innovative', 'breakthrough', 'solution',
        'problem', 'ethics', 'future', 'looking ahead', 'in conclusion'
    ]
    
    question_indicators = [
        'can you tell us', 'can you walk us through', 'what do you see',
        'how does', 'what advice', 'what makes', 'how do you'
    ]
    
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip().lower()
        if len(sentence) < 10:  # Skip very short sentences
            continue
            
        # Estimate timestamp (roughly 3 seconds per sentence)
        timestamp = i * 3
        
        # Detect questions
        for indicator in question_indicators:
            if indicator in sentence:
                up_sots.append({
                    'timestamp': timestamp,
                    'type': 'question',
                    'description': f'Question: {sentence[:100]}...' if len(sentence) > 100 else f'Question: {sentence}',
                    'confidence': 0.8
                })
                break
        
        # Detect key phrases
        for phrase in key_phrases:
            if phrase in sentence and len(sentence) > 30:
                up_sots.append({
                    'timestamp': timestamp,
                    'type': 'key_moment',
                    'description': f'Key point: {sentence[:100]}...' if len(sentence) > 100 else f'Key point: {sentence}',
                    'confidence': 0.7
                })
                break
        
        # Detect topic transitions (sentences starting with specific words)
        topic_starters = ['speaking of', 'looking ahead', 'moving on', 'now', 'finally']
        for starter in topic_starters:
            if sentence.startswith(starter):
                up_sots.append({
                    'timestamp': timestamp,
                    'type': 'topic_transition',
                    'description': f'Topic change: {sentence[:100]}...' if len(sentence) > 100 else f'Topic change: {sentence}',
                    'confidence': 0.9
                })
                break
    
    # Remove duplicates and sort by timestamp
    seen_timestamps = set()
    unique_up_sots = []
    for up_sot in up_sots:
        if up_sot['timestamp'] not in seen_timestamps:
            seen_timestamps.add(up_sot['timestamp'])
            unique_up_sots.append(up_sot)
    
    return sorted(unique_up_sots, key=lambda x: x['timestamp'])

@transcription_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'transcription'})

