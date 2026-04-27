import React, { useEffect, useState } from 'react';
import { Sparkles } from 'lucide-react';

interface Props {
  text: string;
  theme?: string;
  loading?: boolean;
}

export const AiAnnotation: React.FC<Props> = ({ text, theme = "blue", loading = false }) => {
  const [displayText, setDisplayText] = useState("");

  const themeColors: Record<string, string> = {
    blue: '#3b82f6', 
    orange: '#f59e0b', 
    red: '#ef4444', 
    green: '#10b981', 
    purple: '#8b5cf6',
  };
  const activeColor = themeColors[theme] || themeColors.blue;

  useEffect(() => {
    if (loading || !text) {
      setDisplayText("");
      return;
    }
    
    // Typewriter effect
    let i = 0;
    setDisplayText("");
    const intervalId = setInterval(() => {
      setDisplayText(text.substring(0, i));
      i++;
      if (i > text.length) {
        clearInterval(intervalId);
      }
    }, 15);
    
    return () => clearInterval(intervalId);
  }, [text, loading]);

  if (loading) {
    return (
      <div style={{ padding: '1rem', marginTop: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px', borderLeft: `3px solid ${activeColor}`, display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
        <Sparkles size={18} color={activeColor} className="animate-pulse" style={{ flexShrink: 0, marginTop: '2px' }} />
        <span style={{ fontSize: '0.95rem', color: '#64748b', fontStyle: 'italic' }}>AI is analyzing data...</span>
      </div>
    );
  }

  if (!text) return null;

  return (
    <div style={{ padding: '1rem', marginTop: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px', borderLeft: `3px solid ${activeColor}`, display: 'flex', gap: '0.75rem', alignItems: 'flex-start', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
      <Sparkles size={18} color={activeColor} style={{ flexShrink: 0, marginTop: '2px' }} />
      <p style={{ margin: 0, fontSize: '0.95rem', color: '#334155', lineHeight: '1.6' }}>
        {displayText}
        {displayText.length < text.length && <span style={{ borderRight: `2px solid ${activeColor}`, animation: 'blink 1s step-end infinite' }}></span>}
      </p>
    </div>
  );
};
