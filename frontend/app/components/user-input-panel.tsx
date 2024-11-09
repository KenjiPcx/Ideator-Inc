interface UserInputPanelProps {
  email: string;
  setEmail: (email: string) => void;
  input: string;
  handleInputChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  selectedAgent: string | null;
}

export default function UserInputPanel({
  email,
  setEmail,
  input,
  handleInputChange,
  handleSubmit,
  isLoading,
  selectedAgent,
}: UserInputPanelProps) {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-800 p-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex gap-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            className="flex-none w-64 px-4 py-2 rounded bg-gray-700 text-white"
            required
          />
          
          <form onSubmit={handleSubmit} className="flex-1 flex gap-2">
            <textarea
              value={input}
              onChange={handleInputChange}
              placeholder={selectedAgent ? `Talk to ${selectedAgent}...` : 'Select an agent to start...'}
              disabled={!selectedAgent}
              className="flex-1 px-4 py-2 rounded bg-gray-700 text-white resize-none"
              rows={1}
            />
            <button
              type="submit"
              disabled={!selectedAgent || isLoading}
              className="px-6 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
            >
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
} 