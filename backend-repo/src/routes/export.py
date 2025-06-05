from flask import Blueprint, request, jsonify, send_file
import os
import tempfile
import json
from datetime import datetime
import subprocess

export_bp = Blueprint('export', __name__)

@export_bp.route('/export/edl', methods=['POST'])
def export_edl():
    """
    Export up-sots as EDL (Edit Decision List) format
    Compatible with video editing software like Avid, Final Cut Pro, etc.
    """
    try:
        data = request.get_json()
        up_sots = data.get('up_sots', [])
        project_name = data.get('project_name', 'Interview')
        
        if not up_sots:
            return jsonify({'error': 'No up-sots provided'}), 400
        
        # Generate EDL content
        edl_content = generate_edl(up_sots, project_name)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.edl', delete=False) as temp_file:
            temp_file.write(edl_content)
            temp_file_path = temp_file.name
        
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name=f"{project_name}_upsots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.edl",
            mimetype='text/plain'
        )
        
    except Exception as e:
        return jsonify({'error': f'EDL export failed: {str(e)}'}), 500

@export_bp.route('/export/txt', methods=['POST'])
def export_txt():
    """
    Export transcription and up-sots as formatted text file
    """
    try:
        data = request.get_json()
        transcription = data.get('transcription', '')
        up_sots = data.get('up_sots', [])
        project_name = data.get('project_name', 'Interview')
        
        # Generate TXT content
        txt_content = generate_txt(transcription, up_sots, project_name)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(txt_content)
            temp_file_path = temp_file.name
        
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name=f"{project_name}_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mimetype='text/plain'
        )
        
    except Exception as e:
        return jsonify({'error': f'TXT export failed: {str(e)}'}), 500

@export_bp.route('/export/pdf', methods=['POST'])
def export_pdf():
    """
    Export transcription and up-sots as formatted PDF file
    """
    try:
        data = request.get_json()
        transcription = data.get('transcription', '')
        up_sots = data.get('up_sots', [])
        project_name = data.get('project_name', 'Interview')
        
        # Generate Markdown content
        md_content = generate_markdown(transcription, up_sots, project_name)
        
        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as md_file:
            md_file.write(md_content)
            md_file_path = md_file.name
        
        # Create temporary PDF file
        pdf_file_path = md_file_path.replace('.md', '.pdf')
        
        # Convert markdown to PDF using manus utility
        result = subprocess.run(
            ['manus-md-to-pdf', md_file_path, pdf_file_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"PDF conversion failed: {result.stderr}")
        
        # Clean up markdown file
        os.unlink(md_file_path)
        
        return send_file(
            pdf_file_path,
            as_attachment=True,
            download_name=f"{project_name}_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': f'PDF export failed: {str(e)}'}), 500

def generate_edl(up_sots, project_name):
    """
    Generate EDL (Edit Decision List) format content
    EDL format is used by professional video editing software
    """
    edl_lines = []
    
    # EDL Header
    edl_lines.append(f"TITLE: {project_name}")
    edl_lines.append(f"FCM: NON-DROP FRAME")
    edl_lines.append("")
    
    # Sort up-sots by timestamp
    sorted_up_sots = sorted(up_sots, key=lambda x: x.get('timestamp', 0))
    
    for i, up_sot in enumerate(sorted_up_sots, 1):
        timestamp = up_sot.get('timestamp', 0)
        description = up_sot.get('description', 'Key moment')
        up_sot_type = up_sot.get('type', 'key_moment')
        confidence = up_sot.get('confidence', 0.0)
        
        # Convert timestamp to timecode (HH:MM:SS:FF)
        hours = int(timestamp // 3600)
        minutes = int((timestamp % 3600) // 60)
        seconds = int(timestamp % 60)
        frames = int((timestamp % 1) * 30)  # Assuming 30fps
        
        timecode = f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
        
        # EDL entry format
        # Edit number, reel, track, edit type, source in, source out, record in, record out
        edl_lines.append(f"{i:03d}  001      V     C        {timecode} {timecode} {timecode} {timecode}")
        edl_lines.append(f"* FROM CLIP NAME: {up_sot_type.upper()}")
        edl_lines.append(f"* COMMENT: {description}")
        edl_lines.append(f"* CONFIDENCE: {int(confidence * 100)}%")
        edl_lines.append("")
    
    return "\n".join(edl_lines)

def generate_txt(transcription, up_sots, project_name):
    """
    Generate formatted text file content
    """
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append(f"INTERVIEW TRANSCRIPT: {project_name}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")
    
    # Transcription
    lines.append("FULL TRANSCRIPTION:")
    lines.append("-" * 40)
    lines.append(transcription)
    lines.append("")
    lines.append("")
    
    # Up-sots
    if up_sots:
        lines.append("KEY MOMENTS (UP-SOTS):")
        lines.append("-" * 40)
        
        sorted_up_sots = sorted(up_sots, key=lambda x: x.get('timestamp', 0))
        
        for i, up_sot in enumerate(sorted_up_sots, 1):
            timestamp = up_sot.get('timestamp', 0)
            description = up_sot.get('description', 'Key moment')
            up_sot_type = up_sot.get('type', 'key_moment')
            confidence = up_sot.get('confidence', 0.0)
            
            # Format timestamp
            minutes = int(timestamp // 60)
            seconds = int(timestamp % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            
            lines.append(f"{i:2d}. [{time_str}] {up_sot_type.upper()}")
            lines.append(f"    {description}")
            if confidence > 0:
                lines.append(f"    Confidence: {int(confidence * 100)}%")
            lines.append("")
    
    # Footer
    lines.append("=" * 80)
    lines.append("Generated by Retro Professional Transcribe Tool")
    lines.append("=" * 80)
    
    return "\n".join(lines)

def generate_markdown(transcription, up_sots, project_name):
    """
    Generate Markdown content for PDF conversion
    """
    lines = []
    
    # Header
    lines.append(f"# Interview Transcript: {project_name}")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Transcription
    lines.append("## Full Transcription")
    lines.append("")
    lines.append(transcription)
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Up-sots
    if up_sots:
        lines.append("## Key Moments (Up-Sots)")
        lines.append("")
        
        sorted_up_sots = sorted(up_sots, key=lambda x: x.get('timestamp', 0))
        
        for i, up_sot in enumerate(sorted_up_sots, 1):
            timestamp = up_sot.get('timestamp', 0)
            description = up_sot.get('description', 'Key moment')
            up_sot_type = up_sot.get('type', 'key_moment')
            confidence = up_sot.get('confidence', 0.0)
            
            # Format timestamp
            minutes = int(timestamp // 60)
            seconds = int(timestamp % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            
            # Type badge styling
            type_color = {
                'question': '🔵',
                'key_moment': '🟢', 
                'topic_transition': '🟣'
            }.get(up_sot_type, '⚪')
            
            lines.append(f"### {i}. [{time_str}] {type_color} {up_sot_type.replace('_', ' ').title()}")
            lines.append("")
            lines.append(f"**Description:** {description}")
            lines.append("")
            if confidence > 0:
                lines.append(f"**Confidence:** {int(confidence * 100)}%")
                lines.append("")
            lines.append("---")
            lines.append("")
    
    # Footer
    lines.append("## Document Information")
    lines.append("")
    lines.append("- **Tool:** Retro Professional Transcribe Tool")
    lines.append("- **Format:** Professional Interview Transcript")
    lines.append("- **Export Date:** " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    return "\n".join(lines)

@export_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'export'})

