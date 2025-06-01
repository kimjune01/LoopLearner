/**
 * Name generator utilities for automatic naming
 */

const ADJECTIVES = [
  'Brilliant', 'Creative', 'Dynamic', 'Elegant', 'Fantastic', 'Graceful', 'Harmonious', 'Innovative',
  'Joyful', 'Keen', 'Luminous', 'Magnificent', 'Noble', 'Optimistic', 'Peaceful', 'Quick',
  'Radiant', 'Stunning', 'Thoughtful', 'Unique', 'Vibrant', 'Wise', 'Excellent', 'Youthful',
  'Zealous', 'Amazing', 'Bold', 'Clever', 'Delightful', 'Energetic', 'Fluent', 'Gentle'
];

const SIZES = [
  'Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Giant', 'Massive', 'Compact',
  'Mini', 'Big', 'Vast', 'Petite', 'Colossal', 'Immense', 'Micro', 'Macro'
];

const COLORS = [
  'Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange', 'Pink', 'Teal',
  'Crimson', 'Azure', 'Emerald', 'Golden', 'Violet', 'Coral', 'Magenta', 'Turquoise',
  'Scarlet', 'Indigo', 'Lime', 'Amber', 'Lavender', 'Salmon', 'Maroon', 'Navy'
];

const ANIMALS = [
  'Dolphin', 'Eagle', 'Tiger', 'Elephant', 'Penguin', 'Butterfly', 'Lion', 'Owl',
  'Fox', 'Bear', 'Wolf', 'Rabbit', 'Deer', 'Hawk', 'Whale', 'Shark',
  'Leopard', 'Giraffe', 'Zebra', 'Koala', 'Panda', 'Falcon', 'Swan', 'Turtle',
  'Flamingo', 'Cheetah', 'Jaguar', 'Octopus', 'Seahorse', 'Hummingbird', 'Dragonfly', 'Phoenix'
];

/**
 * Generates a random name with the pattern: adjective-size-color-animal
 * Example: "Brilliant-Large-Blue-Dolphin"
 */
export function generateDatasetName(): string {
  const adjective = ADJECTIVES[Math.floor(Math.random() * ADJECTIVES.length)];
  const size = SIZES[Math.floor(Math.random() * SIZES.length)];
  const color = COLORS[Math.floor(Math.random() * COLORS.length)];
  const animal = ANIMALS[Math.floor(Math.random() * ANIMALS.length)];
  
  return `${adjective}-${size}-${color}-${animal}`;
}

/**
 * Generates a human-readable description based on the generated name
 */
export function generateDatasetDescription(name: string): string {
  const parts = name.split('-');
  if (parts.length === 4) {
    const [adjective, size, color, animal] = parts;
    return `A ${adjective.toLowerCase()} evaluation dataset featuring ${size.toLowerCase()} ${color.toLowerCase()} ${animal.toLowerCase()} test cases.`;
  }
  return 'Evaluation dataset for testing prompt performance.';
}

/**
 * Generates both name and description for a dataset
 */
export function generateDatasetNameAndDescription(): { name: string; description: string } {
  const name = generateDatasetName();
  const description = generateDatasetDescription(name);
  return { name, description };
}