// One of these per component with more than one visual state (a dropzone, a file row, a banner, a
// tab bar), named for the component. The markup is built by hand, mirroring index.html, and the
// comment says so, since the two can drift.
import { withCard } from "./utils";

type DropzoneState = "idle" | "dragover" | "rejected";

// Kept in sync with the dropzone markup in index.html.
function buildDropzone(state: DropzoneState): HTMLElement {
  const dz = document.createElement("div");
  dz.id = "dropzone";
  dz.className = "dropzone";
  if (state === "dragover") dz.classList.add("dragover");
  dz.innerHTML = `<div class="dz-inner"><p>Drop a file here, or <button type="button" class="dz-browse">browse</button>.</p>
    <p class="dz-reject" ${state === "rejected" ? "" : "hidden"}>That wasn't a file.</p></div>`;
  return withCard(dz);
}

export default { title: "Components/Dropzone" };

// One export per state, with a human-readable name. Both themes come from the Chromatic modes in
// configs/storybook/preview.ts, so a dark-only regression is caught without a second set of exports.
export const Idle = { name: "Idle", render: () => buildDropzone("idle") };
export const DragOver = { name: "Drag over", render: () => buildDropzone("dragover") };
export const Rejected = { name: "Rejected", render: () => buildDropzone("rejected") };
