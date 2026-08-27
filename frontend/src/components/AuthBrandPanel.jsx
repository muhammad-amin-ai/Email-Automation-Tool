import React from "react";
import { icons } from "./icons.jsx";

const flowNodes = [
  { label: "Contact", icon: icons.users },
  { label: "Template", icon: icons.fileText },
  { label: "Campaign", icon: icons.megaphone },
  { label: "Sent", icon: icons.send },
];

/**
 * The signature visual for the auth screen: a small animated pipeline that
 * mirrors the product's real mechanic (a contact moves through a template
 * into a campaign step and out as a sent email), rather than a decorative
 * illustration unrelated to what the app does.
 */
function AuthFlow() {
  return (
    <div className="auth-flow" aria-hidden="true">
      {flowNodes.map((node, i) => (
        <React.Fragment key={node.label}>
          <div className="auth-flow-node" style={{ animationDelay: `${i * 0.12}s` }}>
            <div className="auth-flow-icon">{node.icon}</div>
            <span>{node.label}</span>
          </div>
          {i < flowNodes.length - 1 && (
            <div className="auth-flow-line">
              <span className="auth-flow-dot" style={{ animationDelay: `${i * 0.5}s` }} />
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

export default function AuthBrandPanel() {
  return (
    <div className="auth-brand">
      <div className="auth-brand-icon">{icons.logoMark}</div>
      <h1>Email automation platform</h1>
      <p>
        Send personalized drip campaigns without the busywork — contacts,
        templates, and scheduling in one place.
      </p>

      <AuthFlow />

      <div className="auth-brand-points">
        <div className="auth-brand-point">
          {icons.check}
          <span>Every email personalized automatically</span>
        </div>
        <div className="auth-brand-point">
          {icons.check}
          <span>Multi-step drip campaigns with scheduling</span>
        </div>
        <div className="auth-brand-point">
          {icons.check}
          <span>AI-drafted templates, ready to edit</span>
        </div>
      </div>
    </div>
  );
}