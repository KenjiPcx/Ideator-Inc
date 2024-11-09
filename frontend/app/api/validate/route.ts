import { openai } from "@ai-sdk/openai";
import { LanguageModelV1, streamText } from "ai";
import { z } from "zod";

// Define the schema for refined idea
const RefinedIdeaSchema = z.object({
  name: z
    .string()
    .describe("The name of the idea if its provided or suggest a creative name"),
  product_summary: z
    .string()
    .describe(
      "A concise summary of the refined idea including the problem statement, product idea, unique value proposition, user story, how it works, and target users"
    ),
  problem_statement: z.string().describe("The detailed problem statement"),
  product_idea: z.string().describe("The detailed product idea"),
  unique_value_proposition: z.string().describe("The detailed unique value proposition"),
  user_story: z.string().describe("The detailed user story"),
  how_it_works: z.string().describe("The detailed how it works"),
  target_users: z.string().describe("The detailed target users"),
});

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = await streamText({
    model: openai("gpt-4o-mini") as LanguageModelV1,
    messages: [
      {
        role: "system",
        content: `
        ### Base Context
        You are a helpful assistant, you think step by step in a observation thought action loop.

        ### Context
        You are part of a research team that does autonomous research on a user's startup idea.
        You are the entrypoint to the research team, sometimes users give too generic ideas and lack basic details that waste the research team's time. Your goal is to ensure that the startup idea is defined enough to be researched, you don't need every detail from the user, but you will need to do a basic validation and ask users for as much detail as possible (if they have it) before passing it on to the research team.

        Follow these steps:
        1. Repeat back the user's idea from what you understand, call the "update_idea" tool to extract the idea you understood and show it to the user. Then ask follow up questions to gather more information. You must call the "update_idea" tool before asking follow up questions.
        2. After the user confirms the refinements are accurate, call the "confirm_idea" tool to lock the idea and unlock the research phase, communicate that the idea can't be edited after confirmation
        3. Call the "start_research" tool to start the research phase, and notify the user that the research team will start working on the idea and end the chat.

        Note:
        - The user might not be able to provide the information to your questions, and that is okay, the research team will look into that, we still ask the question just in case the user can provide information early on and make the research more accurate
        - The user can edit the idea anytime before the idea is confirmed

        Guidelines:
        - Ask one question at a time
        - Focus on problem validation first
        - Request specific examples and use cases
        - Verify market need and target users
        - Keep responses concise but informative
        - Use "update_idea" tool only when you have enough information
        - Use "confirm_idea" tool only after user explicitly agrees with the refined idea`,
      },
      ...messages,
    ],
    tools: {
      update_idea: {
        description:
          "Update the displayed idea details from what you have gathered from the user",
        parameters: RefinedIdeaSchema,
      },
      confirm_idea: {
        description: "Confirm the idea is validated and ready for research",
        parameters: z.object({}),
      },
      start_research: {
        description: "Start the research phase",
        parameters: z.object({}),
      },
    },
    maxSteps: 3,
  });

  return result.toDataStreamResponse();
}
