import React from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import {
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { 
  GripVertical, 
  Briefcase, 
  GraduationCap, 
  Lightbulb, 
  Award, 
  Globe,
  Settings2,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

export interface SectionConfig {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
  visible: boolean;
}

interface SectionOrderManagerProps {
  sections: SectionConfig[];
  onSectionsChange: (sections: SectionConfig[]) => void;
}

interface SortableItemProps {
  id: string;
  section: SectionConfig;
  onToggleVisibility: (id: string) => void;
}

const SortableItem: React.FC<SortableItemProps> = ({ id, section, onToggleVisibility }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-3 p-3 rounded-lg border ${
        section.visible 
          ? 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700' 
          : 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 opacity-60'
      } transition-all hover:shadow-md`}
    >
      <button
        className="cursor-move touch-none p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
        {...attributes}
        {...listeners}
      >
        <GripVertical className="h-5 w-5 text-gray-400" />
      </button>
      
      <div className={`p-2 rounded-lg ${section.color}`}>
        {section.icon}
      </div>
      
      <span className="flex-1 font-medium text-sm">{section.name}</span>
      
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onToggleVisibility(id)}
        className="h-8 px-3 text-xs"
      >
        {section.visible ? 'Hide' : 'Show'}
      </Button>
    </div>
  );
};

export const SectionOrderManager: React.FC<SectionOrderManagerProps> = ({
  sections,
  onSectionsChange,
}) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [localSections, setLocalSections] = React.useState(sections);
  const [isExpanded, setIsExpanded] = React.useState(false);

  React.useEffect(() => {
    setLocalSections(sections);
  }, [sections]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = localSections.findIndex((s) => s.id === active.id);
      const newIndex = localSections.findIndex((s) => s.id === over.id);
      
      const newSections = arrayMove(localSections, oldIndex, newIndex);
      setLocalSections(newSections);
      onSectionsChange(newSections);
    }
  };

  const handleToggleVisibility = (id: string) => {
    const newSections = localSections.map(section =>
      section.id === id ? { ...section, visible: !section.visible } : section
    );
    setLocalSections(newSections);
    onSectionsChange(newSections);
  };

  const handleApply = () => {
    onSectionsChange(localSections);
    setIsOpen(false);
  };

  // Mini view for inline section management
  const MiniView = () => (
    <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Settings2 className="h-4 w-4" />
          <span>Section Order</span>
        </div>
        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>
      
      {isExpanded && (
        <div className="mt-3 space-y-2">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={localSections.map(s => s.id)}
              strategy={verticalListSortingStrategy}
            >
              {localSections.map((section) => (
                <SortableItem
                  key={section.id}
                  id={section.id}
                  section={section}
                  onToggleVisibility={handleToggleVisibility}
                />
              ))}
            </SortableContext>
          </DndContext>
        </div>
      )}
    </div>
  );

  return (
    <>
      <MiniView />
      
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Customize Section Order</DialogTitle>
            <DialogDescription>
              Drag and drop to reorder sections. Toggle visibility as needed.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-2 mt-4">
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={localSections.map(s => s.id)}
                strategy={verticalListSortingStrategy}
              >
                {localSections.map((section) => (
                  <SortableItem
                    key={section.id}
                    id={section.id}
                    section={section}
                    onToggleVisibility={handleToggleVisibility}
                  />
                ))}
              </SortableContext>
            </DndContext>
          </div>
          
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleApply}>
              Apply Changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};