import { JSONValue } from "ai";
import React from "react";
import { DocumentFile } from ".";
import { Button } from "../button";
import { DocumentPreview } from "../document-preview";
import FileUploader from "../file-uploader";
import { Textarea } from "../textarea";
import UploadImagePreview from "../upload-image-preview";
import { ChatHandler } from "./chat.interface";
import { useFile } from "./hooks/use-file";
import { LlamaCloudSelector } from "./widgets/LlamaCloudSelector";
import { Send, Loader2 } from "lucide-react";
import { cn } from "../../../lib/utils";
import { buttonVariants } from "../button";

const ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "csv", "pdf", "txt", "docx"];

export default function ChatInput(
  props: Pick<
    ChatHandler,
    | "isLoading"
    | "input"
    | "onFileUpload"
    | "onFileError"
    | "handleSubmit"
    | "handleInputChange"
    | "messages"
    | "setInput"
    | "append"
  > & {
    requestParams?: any;
    setRequestData?: React.Dispatch<any>;
  },
) {
  const {
    imageUrl,
    setImageUrl,
    uploadFile,
    files,
    removeDoc,
    reset,
    getAnnotations,
  } = useFile();

  // default submit function does not handle including annotations in the message
  // so we need to use append function to submit new message with annotations
  const handleSubmitWithAnnotations = (
    e: React.FormEvent<HTMLFormElement>,
    annotations: JSONValue[] | undefined,
  ) => {
    e.preventDefault();
    props.append!({
      content: props.input,
      role: "user",
      createdAt: new Date(),
      annotations,
    });
    props.setInput!("");
  };

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const annotations = getAnnotations();
    if (annotations.length) {
      handleSubmitWithAnnotations(e, annotations);
      return reset();
    }
    props.handleSubmit(e);
  };

  const handleUploadFile = async (file: File) => {
    if (imageUrl) {
      alert("You can only upload one image at a time.");
      return;
    }
    try {
      await uploadFile(file, props.requestParams);
      props.onFileUpload?.(file);
    } catch (error: any) {
      const onFileUploadError = props.onFileError || window.alert;
      onFileUploadError(error.message);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit(e as unknown as React.FormEvent<HTMLFormElement>);
    }
    // Auto-adjust height
    const textarea = e.currentTarget;
    textarea.style.height = 'inherit';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`; // Max height of 200px
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    props.handleInputChange(e);
    // Auto-adjust height
    const textarea = e.currentTarget;
    textarea.style.height = 'inherit';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`; // Max height of 200px
  };

  return (
    <form
      onSubmit={onSubmit}
      className="rounded-lg bg-gray-800 p-4 space-y-4 shrink-0 border border-gray-700 text-white"
    >
      {imageUrl && (
        <UploadImagePreview url={imageUrl} onRemove={() => setImageUrl(null)} />
      )}
      {files.length > 0 && (
        <div className="flex gap-4 w-full overflow-auto py-2">
          {files.map((file: DocumentFile) => (
            <DocumentPreview
              key={file.id}
              file={file}
              onRemove={() => removeDoc(file)}
            />
          ))}
        </div>
      )}
      <div className="flex w-full items-end justify-between gap-4">
        <Textarea
          id="chat-input"
          autoFocus
          name="message"
          placeholder="Type a message"
          className="flex-1 min-h-[40px] max-h-[200px] bg-gray-700 border-gray-600 placeholder-gray-400 text-white focus:border-gray-500 focus:ring-0 overflow-y-auto resize-none"
          value={props.input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          rows={1}
        />
        <FileUploader
          onFileUpload={handleUploadFile}
          onFileError={props.onFileError}
          config={{
            allowedExtensions: ALLOWED_EXTENSIONS,
            disabled: props.isLoading,
          }}
        />
        {process.env.NEXT_PUBLIC_USE_LLAMACLOUD === "true" &&
          props.setRequestData && (
            <LlamaCloudSelector setRequestData={props.setRequestData} />
          )}
        <Button
          type="submit"
          disabled={props.isLoading || !props.input.trim()}
          className={cn(
            buttonVariants({ variant: "secondary", size: "icon" }),
            "bg-gray-700 hover:bg-gray-600 text-white disabled:text-gray-400 self-stretch",
          )}
        >
          {props.isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
    </form>
  );
}
