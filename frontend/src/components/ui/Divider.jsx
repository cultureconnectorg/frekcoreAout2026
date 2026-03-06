export function Divider({ className = '' }) {
  return (
    <div
      className={`h-px bg-gradient-to-r from-transparent via-terra/50 to-transparent ${className}`}
    />
  );
}

export default Divider;
