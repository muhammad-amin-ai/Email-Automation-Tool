import React, { createContext, useCallback, useContext, useRef, useState } from "react";

const ConfirmContext = createContext(null);

/**
 * Renders the app's own confirm dialog instead of the browser's native
 * confirm() popup, so destructive actions (delete contact/template/campaign)
 * match the rest of the UI instead of breaking out into an OS-styled box.
 */
export function ConfirmProvider({ children }) {
  const [state, setState] = useState(null); // { message, confirmLabel, danger }
  const resolver = useRef(null);

  const confirmAction = useCallback((message, options = {}) => {
    setState({
      message,
      confirmLabel: options.confirmLabel || "Delete",
      danger: options.danger !== false,
    });
    return new Promise((resolve) => {
      resolver.current = resolve;
    });
  }, []);

  const handle = (result) => {
    setState(null);
    if (resolver.current) {
      resolver.current(result);
      resolver.current = null;
    }
  };

  return (
    <ConfirmContext.Provider value={confirmAction}>
      {children}
      {state && (
        <div className="confirm-overlay" onClick={() => handle(false)}>
          <div
            className="confirm-dialog"
            role="alertdialog"
            aria-modal="true"
            onClick={(e) => e.stopPropagation()}
          >
            <p className="confirm-message">{state.message}</p>
            <div className="confirm-actions">
              <button className="btn secondary" onClick={() => handle(false)}>
                Cancel
              </button>
              <button
                className={state.danger ? "btn danger" : "btn"}
                onClick={() => handle(true)}
                autoFocus
              >
                {state.confirmLabel}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

// Returns an async function: `if (!(await confirmAction("Delete this?"))) return;`
export function useConfirm() {
  return useContext(ConfirmContext);
}
