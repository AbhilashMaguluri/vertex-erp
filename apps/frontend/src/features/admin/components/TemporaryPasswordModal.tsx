import * as React from 'react';
import { Modal } from '@/shared/components/ui/Modal';
import { Button } from '@/shared/components/ui/Button';
import { Copy, Check, Mail } from 'lucide-react';

interface TemporaryPasswordModalProps {
  open: boolean;
  onClose: () => void;
  email: string;
  temporaryPassword: string;
  emailSent: boolean;
}

export function TemporaryPasswordModal({ open, onClose, email, temporaryPassword, emailSent }: TemporaryPasswordModalProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(temporaryPassword);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Temporary Password"
      description={`Share this with ${email} through a secure channel. It will not be shown again.`}
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between rounded-md border border-border bg-muted/50 px-3 py-2 font-mono text-sm">
          <span>{temporaryPassword}</span>
          <button onClick={handleCopy} className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Copy password">
            {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
          </button>
        </div>

        {emailSent ? (
          <div className="flex items-center gap-2 rounded-md bg-emerald-50 dark:bg-emerald-950 p-3 text-xs font-medium text-emerald-700 dark:text-emerald-300">
            <Mail className="h-4 w-4 shrink-0" />
            <span>Also emailed to {email}.</span>
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">
            Email delivery isn't configured for this environment — deliver this password to the user
            yourself (in person, chat, etc.).
          </p>
        )}

        <div className="flex justify-end">
          <Button onClick={onClose}>Done</Button>
        </div>
      </div>
    </Modal>
  );
}
