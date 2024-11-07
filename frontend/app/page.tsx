'use client'

import ChatSection from "./components/chat-section";

export default function Home() {
  const handleFirstMessage = (sessionId: string) => {
    // Update URL without triggering a navigation
    window.history.pushState({}, '', `/research/${sessionId}`);
  };

  return (
    <main className="h-screen w-screen flex justify-center items-center background-gradient">
      <div className="space-y-2 lg:space-y-10 w-[90%] lg:w-[60rem]">
        <div className="h-[65vh] flex">
          <ChatSection onFirstMessage={handleFirstMessage} />
        </div>
      </div>
    </main>
  );
}
