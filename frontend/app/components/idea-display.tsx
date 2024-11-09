import { useState } from "react";

export type RefinedIdea = {
  name: string;
  product_summary: string;
  problem_statement: string;
  product_idea: string;
  unique_value_proposition: string;
  user_story: string;
  how_it_works: string;
  target_users: string;
};

interface IdeaDisplayProps {
  idea: RefinedIdea | null;
  isValidated: boolean;
}

export default function IdeaDisplay({ idea, isValidated }: IdeaDisplayProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  if (!idea) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 text-white h-full flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">No Idea Yet</h2>
          <p className="text-gray-400">
            Talk to the Idea Validator to get started
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="h-full ">
        <div className="bg-gray-800 rounded-lg p-6 text-white h-full flex flex-col justify-between">
          <div className="flex items-center justify-between flex-0">
            <p className="text-2xl font-bold mb-4">
              {idea.name || "Your Startup Idea"}
            </p>
            {isValidated && (
              <span className="px-3 py-1 bg-green-500 text-white rounded-full text-sm">
                Validated
              </span>
            )}
          </div>

          <div className="overflow-hidden flex-1 flex flex-col justify-around space-y-4">
            <p className="text-gray-300 line-clamp-3">
              {idea.product_summary}
            </p>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="flex-0 mt-4 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
          >
            View Full Details
          </button>
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white">
                Startup Idea Details
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              {Object.entries(idea).map(([key, value]) => (
                <div key={key}>
                  <h3 className="font-semibold mb-2 text-white capitalize">
                    {key.replace(/_/g, " ")}
                  </h3>
                  <p className="text-gray-300">{value}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
