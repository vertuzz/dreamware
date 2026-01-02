import type { Tag, Tool, Dream } from '~/lib/types';
import MultiSelect from '~/components/common/MultiSelect';

interface FilterBarProps {
    tags: Tag[];
    tools: Tool[];
    selectedTagIds: number[];
    selectedToolIds: number[];
    selectedStatuses: Dream['status'][];
    onChange: (selected: { tagIds: number[]; toolIds: number[]; statuses: Dream['status'][] }) => void;
}

const statusOptions: { id: string; name: string }[] = [
    { id: 'Concept', name: 'Concept' },
    { id: 'WIP', name: 'WIP' },
    { id: 'Live', name: 'Live' },
];

export default function FilterBar({
    tags,
    tools,
    selectedTagIds,
    selectedToolIds,
    selectedStatuses,
    onChange,
}: FilterBarProps) {
    const handleTagsChange = (newTagIds: number[]) => {
        onChange({ tagIds: newTagIds, toolIds: selectedToolIds, statuses: selectedStatuses });
    };

    const handleToolsChange = (newToolIds: number[]) => {
        onChange({ tagIds: selectedTagIds, toolIds: newToolIds, statuses: selectedStatuses });
    };

    const handleStatusChange = (newStatusIds: any[]) => {
        // MultiSelect uses numbers for IDs internally, but our statuses are strings.
        // We'll map them.
        onChange({
            tagIds: selectedTagIds,
            toolIds: selectedToolIds,
            statuses: newStatusIds as Dream['status'][]
        });
    };

    // Prepare status items for MultiSelect
    // MultiSelect expects {id: number, name: string}
    // We'll use a hacky way since MultiSelect is typed with number ids
    const statusItems = statusOptions.map(opt => ({
        id: opt.id as unknown as number,
        name: opt.name
    }));

    return (
        <div className="flex items-center gap-2">
            <MultiSelect
                label="Status"
                icon="flag"
                placeholder="Filter by status..."
                items={statusItems}
                selectedIds={selectedStatuses as unknown as number[]}
                onChange={handleStatusChange}
                color="primary"
            />
            <MultiSelect
                label="Tags"
                icon="sell"
                placeholder="Search tags..."
                items={tags}
                selectedIds={selectedTagIds}
                onChange={handleTagsChange}
                color="primary"
            />
            <MultiSelect
                label="Tools"
                icon="build"
                placeholder="Search tools..."
                items={tools}
                selectedIds={selectedToolIds}
                onChange={handleToolsChange}
                color="purple"
            />
        </div>
    );
}


