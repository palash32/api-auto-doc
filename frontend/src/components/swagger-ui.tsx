'use client';

import dynamic from 'next/dynamic';
import 'swagger-ui-react/swagger-ui.css';

const SwaggerUI = dynamic(() => import('swagger-ui-react'), { ssr: false });

interface SwaggerViewerProps {
    spec: Record<string, unknown>;
}

export default function SwaggerViewer({ spec }: SwaggerViewerProps) {
    return (
        <div className="swagger-wrapper bg-white rounded-lg overflow-hidden">
            <SwaggerUI spec={spec} />
        </div>
    );
}
