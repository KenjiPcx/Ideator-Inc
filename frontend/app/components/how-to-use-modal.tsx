interface HowToUseModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function HowToUseModal({ isOpen, onClose }: HowToUseModalProps) {
  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center"
      onClick={onClose}
    >
      <div 
        className="bg-gray-800 p-8 rounded-lg max-w-2xl w-full mx-4 space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-2xl font-bold text-white">How to Use</h2>
        <div className="space-y-3 text-gray-200">
          <p>Welcome to the Ideator Inc! The home for autonomous AI research teams. Here's how to get started:</p>
          <ol className="list-decimal list-inside space-y-2">
            <li>Start by clicking on the <b>Research Manager</b> to share your startup idea</li>
            <li>The AI will help refine and validate your idea</li>
            <li>Once validated, click <b>Start Research</b> on the bottom right to begin the AI research process</li>
            <li>Watch as different research teams analyze your idea</li>
            <li>You can click on the agent cards to see the research they are doing</li>
            <li>When research is complete, chat with the <b>Research Assistant</b> to learn about the findings</li>
          </ol>
          <p className="text-sm text-gray-400 mt-4">You can also try a demo idea by clicking the "Demo Idea" button</p>
        </div>
        <button 
          onClick={onClose}
          className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg transition-colors"
        >
          Got it!
        </button>
      </div>
    </div>
  );
} 