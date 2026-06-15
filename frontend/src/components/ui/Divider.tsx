/** Ornamental serif divider (✧ ✧ ✧) between major sections. */
export function Divider() {
  return (
    <div
      className="py-8 text-center font-serif text-2xl tracking-[1em] text-neutral-400"
      aria-hidden="true"
    >
      &#x2727; &#x2727; &#x2727;
    </div>
  );
}
