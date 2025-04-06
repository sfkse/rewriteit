def parse_command(text: str) -> tuple[str, str | None]:
    """
    Parse the text to extract the text to rephrase and optional tone.
    Format: "--tone informal do not rephrase this" or "do not rephrase this --tone informal"
    """
    # Find the last occurrence of --tone
    tone_index = text.rfind("--tone")
    
    if tone_index == -1:
        # No --tone found, return the whole text
        return text.strip(), None
    
    # Split the text into parts before and after --tone
    before_tone = text[:tone_index].strip()
    after_tone = text[tone_index + len("--tone"):].strip()
    # Get the tone (first word after --tone)
    tone_words = after_tone.split()
    tone = tone_words[0] if tone_words else None
    # Get the actual text (everything before --tone and after the tone word)
    actual_text = before_tone
    if len(tone_words) > 1:
        actual_text = (before_tone + " " + " ".join(tone_words[1:])).strip()
    return actual_text, tone