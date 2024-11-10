"use client";

interface FooterProps {
  sessionId: string;
}

export default function Footer({ sessionId }: FooterProps) {
  return (
    <footer className="mt-2">
      <span className="text-gray-400 text-sm">Session: {sessionId}</span>
    </footer>
  );
} 