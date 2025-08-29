import React from 'react';
import { Check, Circle, Loader2, Brain, MessageSquare, Wrench, Database, FileText } from 'lucide-react';

export interface Stage {
  id: string;
  name: string;
  status: 'pending' | 'active' | 'completed';
  description?: string;
}

interface StageProgressIndicatorProps {
  stages: Stage[];
  currentStage?: string;
  isCompact?: boolean;
}

const stageIcons: Record<string, React.FC<{ className?: string }>> = {
  initialization: Brain,
  conversation: MessageSquare,
  tool_execution: Wrench,
  data_persistence: Database,
  response_formatting: FileText,
};

const stageDisplayNames: Record<string, string> = {
  initialization: 'Initializing',
  conversation: 'Processing Request',
  tool_execution: 'Executing Tools',
  data_persistence: 'Saving Data',
  response_formatting: 'Formatting Response',
};

export const StageProgressIndicator: React.FC<StageProgressIndicatorProps> = ({
  stages,
  currentStage,
  isCompact = false,
}) => {
  // Update stage statuses based on current stage
  const processedStages = stages.map((stage) => {
    if (currentStage) {
      const currentIndex = stages.findIndex(s => s.id === currentStage);
      const stageIndex = stages.findIndex(s => s.id === stage.id);
      
      if (stageIndex < currentIndex) {
        return { ...stage, status: 'completed' as const };
      } else if (stageIndex === currentIndex) {
        return { ...stage, status: 'active' as const };
      }
    }
    return stage;
  });

  if (isCompact) {
    const activeStage = processedStages.find(s => s.status === 'active');
    const completedCount = processedStages.filter(s => s.status === 'completed').length;
    
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-white/80 backdrop-blur-sm rounded-lg border border-gray-200/50">
        <div className="flex items-center gap-1.5">
          {activeStage && (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-500" />
              <span className="text-xs font-medium text-gray-700">
                {stageDisplayNames[activeStage.id] || activeStage.name}
              </span>
            </>
          )}
          {!activeStage && completedCount === stages.length && (
            <>
              <Check className="w-3.5 h-3.5 text-green-500" />
              <span className="text-xs font-medium text-gray-700">Complete</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-0.5 ml-auto">
          {processedStages.map((stage, index) => (
            <div
              key={stage.id}
              className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${
                stage.status === 'completed' 
                  ? 'bg-green-500' 
                  : stage.status === 'active' 
                  ? 'bg-blue-500 animate-pulse' 
                  : 'bg-gray-300'
              }`}
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3 p-4 bg-white/90 backdrop-blur-sm rounded-lg border border-gray-200/50">
      {processedStages.map((stage, index) => {
        const Icon = stageIcons[stage.id] || Circle;
        const isLast = index === stages.length - 1;
        
        return (
          <div key={stage.id} className="relative">
            <div className="flex items-start gap-3">
              {/* Icon and line */}
              <div className="relative flex flex-col items-center">
                <div className={`
                  w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300
                  ${stage.status === 'completed' 
                    ? 'bg-green-100 border-2 border-green-500' 
                    : stage.status === 'active' 
                    ? 'bg-blue-100 border-2 border-blue-500 animate-pulse' 
                    : 'bg-gray-100 border-2 border-gray-300'}
                `}>
                  {stage.status === 'completed' ? (
                    <Check className="w-4 h-4 text-green-600" />
                  ) : stage.status === 'active' ? (
                    <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                  ) : (
                    <Icon className="w-4 h-4 text-gray-400" />
                  )}
                </div>
                {!isLast && (
                  <div className={`
                    absolute top-8 w-0.5 h-8 transition-all duration-300
                    ${stage.status === 'completed' ? 'bg-green-400' : 'bg-gray-200'}
                  `} />
                )}
              </div>
              
              {/* Stage info */}
              <div className="flex-1 pt-1">
                <div className="flex items-center gap-2">
                  <span className={`
                    text-sm font-medium transition-colors duration-300
                    ${stage.status === 'completed' 
                      ? 'text-green-700' 
                      : stage.status === 'active' 
                      ? 'text-blue-700' 
                      : 'text-gray-500'}
                  `}>
                    {stageDisplayNames[stage.id] || stage.name}
                  </span>
                  {stage.status === 'active' && (
                    <div className="flex gap-0.5">
                      <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  )}
                </div>
                {stage.description && (
                  <p className="text-xs text-gray-500 mt-0.5">{stage.description}</p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};