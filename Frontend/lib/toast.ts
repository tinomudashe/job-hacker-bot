import { toast as sonnerToast } from "sonner";

// Enhanced toast function that works as both function and object
function createToast(message: string, options?: any) {
  return sonnerToast(message, {
    ...options,
    // Remove automatic dismiss action to let Sonner handle its own close button
    action: options?.action,
  });
}

// Add methods to the function
createToast.success = (message: string, options?: any) => {
  return sonnerToast.success(message, {
    ...options,
    // Remove automatic dismiss action to let Sonner handle its own close button
    action: options?.action,
  });
};

createToast.error = (message: string, options?: any) => {
  return sonnerToast.error(message, {
    ...options,
    // Remove automatic dismiss action to let Sonner handle its own close button
    action: options?.action,
  });
};

createToast.info = (message: string, options?: any) => {
  return sonnerToast.info(message, {
    ...options,
    // Remove automatic dismiss action to let Sonner handle its own close button
    action: options?.action,
  });
};

createToast.warning = (message: string, options?: any) => {
  return sonnerToast.warning(message, {
    ...options,
    // Remove automatic dismiss action to let Sonner handle its own close button
    action: options?.action,
  });
};

createToast.promise = sonnerToast.promise;
createToast.loading = sonnerToast.loading;

// Dismiss functions - Fixed to properly handle individual toast dismissal
createToast.dismiss = (toastId?: string | number) => {
  if (toastId) {
    // Dismiss specific toast
    sonnerToast.dismiss(toastId);
  } else {
    // If no ID provided, dismiss the most recent toast
    sonnerToast.dismiss();
  }
};

// Fixed dismissAll to properly dismiss all toasts
createToast.dismissAll = () => {
  // Get all visible toasts and dismiss them
  const toastContainer = document.querySelector("[data-sonner-toaster]");
  if (toastContainer) {
    // Sonner uses data-sonner-toast attribute for each toast
    const toasts = toastContainer.querySelectorAll("[data-sonner-toast]");
    toasts.forEach(() => {
      sonnerToast.dismiss();
    });
  }
  // Also call the general dismiss to ensure all are cleared
  sonnerToast.dismiss();
};

// Custom dismiss with confirmation for important messages
createToast.dismissWithConfirm = (
  toastId: string | number,
  message = "Are you sure you want to dismiss this notification?"
) => {
  if (confirm(message)) {
    sonnerToast.dismiss(toastId);
  }
};

// Add a method to create dismissible toasts with custom actions
createToast.dismissible = (message: string, options?: any) => {
  const toastId = sonnerToast(message, {
    ...options,
    action: options?.action || {
      label: "Dismiss",
      onClick: () => sonnerToast.dismiss(toastId),
    },
  });
  return toastId;
};

export const toast = createToast;

// Keyboard shortcut to dismiss all toasts (Ctrl/Cmd + Shift + X)
if (typeof window !== "undefined") {
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === "X") {
      e.preventDefault();
      toast.dismissAll();
      // Use a timeout to ensure the dismiss all completes before showing the success message
      setTimeout(() => {
        sonnerToast.success("All notifications dismissed", {
          duration: 2000,
          // Don't add auto-dismiss action to this confirmation toast
        });
      }, 100);
    }
  });
}
