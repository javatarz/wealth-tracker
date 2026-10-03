import { useState, type DragEvent } from "react";

interface DropZoneProps {
  disabled: boolean;
  onFile: (file: File) => void;
}

export function DropZone({ disabled, onFile }: DropZoneProps) {
  const [dragging, setDragging] = useState(false);

  function accept(files: FileList | null) {
    const file = files?.[0];
    if (file && !disabled) {
      onFile(file);
    }
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    accept(event.dataTransfer.files);
  }

  return (
    <div
      className={`dropzone${dragging ? " dragging" : ""}`}
      data-testid="dropzone"
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(!disabled);
      }}
      onDragLeave={() => {
        setDragging(false);
      }}
      onDrop={onDrop}
    >
      <p>Drop a CAMS or KFintech Consolidated Account Statement PDF here</p>
      <FilePicker disabled={disabled} onFiles={accept} />
      <p className="muted small">
        The file is read on this machine and discarded. Nothing is stored.
      </p>
    </div>
  );
}

interface FilePickerProps {
  disabled: boolean;
  onFiles: (files: FileList | null) => void;
}

function FilePicker({ disabled, onFiles }: FilePickerProps) {
  return (
    <label className={`btn${disabled ? " disabled" : ""}`}>
      Choose file
      <input
        type="file"
        accept="application/pdf,.pdf"
        className="visually-hidden"
        disabled={disabled}
        onChange={(event) => {
          onFiles(event.target.files);
          event.target.value = "";
        }}
      />
    </label>
  );
}
