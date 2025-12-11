import emailjs from '@emailjs/browser';

// Initialize EmailJS (call this in layout or app entry)
export const initEmailJS = () => {
    // Replace with your actual public key
    if (process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY) {
        emailjs.init(process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY);
    }
};

interface FeedbackData {
    message: string;
    type: "bug" | "feature" | "other";
}

export const sendFeedback = async (data: FeedbackData) => {
    const serviceId = process.env.NEXT_PUBLIC_EMAILJS_SERVICE_ID;
    const templateId = process.env.NEXT_PUBLIC_EMAILJS_TEMPLATE_ID;
    const publicKey = process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY;

    if (!serviceId || !templateId || !publicKey) {
        console.warn("EmailJS not configured. Logging feedback to console:");
        console.warn("EmailJS not configured. Logging feedback to console (DEV MODE):", data);
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        return;
    }

    try {
        await emailjs.send(
            serviceId,
            templateId,
            {
                type: data.type,
                message: data.message,
                timestamp: new Date().toLocaleString(),
                url: window.location.href,
                userAgent: navigator.userAgent
            },
            publicKey
        );
    } catch (error) {
        console.error("EmailJS Error:", error);
        throw error;
    }
};
