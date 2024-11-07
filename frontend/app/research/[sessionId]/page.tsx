import ChatSection from "../../components/chat-section";

export default function ChatSession({
  params,
}: {
  params: { sessionId: string };
}) {
  return (
    <main className="h-screen w-screen flex justify-center items-center background-gradient">
      <div className="space-y-2 lg:space-y-10 w-[90%] lg:w-[60rem]">
        <div className="h-[65vh] flex">
          <ChatSection sessionId={params.sessionId} />
        </div>
      </div>
    </main>
  );
} 