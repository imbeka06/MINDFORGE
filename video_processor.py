from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def get_video_id(url):
    """
    Extracts the video ID from a YouTube URL.
    Examples:
    - https://www.youtube.com/watch?v=dQw4w9WgXcQ -> dQw4w9WgXcQ
    - https://youtu.be/dQw4w9WgXcQ -> dQw4w9WgXcQ
    """
    query = urlparse(url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            p = parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    return None

def process_video(video_url):
    """
    Fetches the transcript of a YouTube video and chunks it.
    """
    video_id = get_video_id(video_url)
    if not video_id:
        return None

    try:
        # 1. Fetch Transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # 2. Combine into full text
        full_text = " ".join([item['text'] for item in transcript_list])
        
        # 3. Create simple chunks (same logic as PDF)
        chunk_size = 4000
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        
        return {
            "filename": f"Video_{video_id}",
            "full_text": full_text,
            "chunks": chunks,
            "chunk_count": len(chunks)
        }
    except Exception as e:
        print(f"Video Error: {e}")
        return None