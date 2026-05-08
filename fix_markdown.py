import sys, re
paths = [
    'e:/SmartStudy-AI/frontend/pages/dashboard.py',
    'e:/SmartStudy-AI/frontend/pages/session.py',
    'e:/SmartStudy-AI/frontend/pages/analytics.py',
    'e:/SmartStudy-AI/frontend/pages/insights.py',
    'e:/SmartStudy-AI/frontend/pages/settings.py',
    'e:/SmartStudy-AI/frontend/components/focus_indicator.py',
    'e:/SmartStudy-AI/frontend/components/timer_display.py',
    'e:/SmartStudy-AI/frontend/components/alert_popup.py',
    'e:/SmartStudy-AI/frontend/app.py'
]

for p in paths:
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()
    
    import textwrap
    
    def replacer(match):
        inner = match.group(1)
        # To avoid being parsed as markdown code blocks inside Streamlit HTML,
        # we completely dedent everything, and ensure no lines start with 4 spaces.
        dedented = textwrap.dedent(inner)
        # Also remove any line breaks within style tags that might cause trouble (optional),
        # but just taking out the 4-space indent fixes 99% of markdown escaping issues.
        lines = []
        for line in dedented.split('\n'):
            line = line.strip()  # Strip everything to be super safe
            if line:
                lines.append(line)
        return 'st.markdown("""\n' + '\n'.join(lines) + '\n""", unsafe_allow_html=True)'
    
    new_content = re.sub(r'st\.markdown\("""(.*?)""", unsafe_allow_html=True\)', replacer, content, flags=re.DOTALL)
    
    # Also replace f-strings
    new_content = re.sub(r'st\.markdown\(f"""(.*?)""", unsafe_allow_html=True\)', 
                         lambda m: 'st.markdown(f"""\n' + '\n'.join(line.strip() for line in textwrap.dedent(m.group(1)).split('\n') if line.strip()) + '\n""", unsafe_allow_html=True)', 
                         new_content, flags=re.DOTALL)

    if new_content != content:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Fixed {p}')
