import { useState, type SubmitEvent } from "react";

const TONE_CLASS = { neutral: undefined, bad: "bad-text" } as const;

interface PasswordPromptProps {
  fileName: string;
  message: string;
  tone: keyof typeof TONE_CLASS;
  onSubmit: (password: string) => void;
}

export function PasswordPrompt({
  fileName,
  message,
  tone,
  onSubmit,
}: PasswordPromptProps) {
  const [password, setPassword] = useState("");

  function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(password);
  }

  return (
    <form className="callout" onSubmit={submit}>
      <p role="alert" className={TONE_CLASS[tone]}>
        {message} Enter its password to open {fileName}.
      </p>
      <label>
        Statement password
        <input
          type="password"
          autoComplete="off"
          value={password}
          onChange={(event) => {
            setPassword(event.target.value);
          }}
        />
      </label>
      <button type="submit" className="btn btn-primary" disabled={!password}>
        Open statement
      </button>
    </form>
  );
}
