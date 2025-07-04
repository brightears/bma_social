export interface QuotationTemplate {
  id: string;
  name: string;
  title: string;
  description: string;
  items: {
    description: string;
    quantity: number;
    unit_price: number;
  }[];
  notes?: string;
}

export const quotationTemplates: QuotationTemplate[] = [
  {
    id: 'soundtrack-app-subscription',
    name: 'Soundtrack App Subscription (12 months + Service)',
    title: 'Soundtrack App Subscription - 12 Months',
    description: 'Professional background music solution for your business with 12-month subscription including setup and support services.',
    items: [
      {
        description: 'Soundtrack App Subscription (12 months)',
        quantity: 1,
        unit_price: 12000,
      },
      {
        description: 'Initial Setup and Configuration Service',
        quantity: 1,
        unit_price: 3000,
      },
      {
        description: 'On-site Training and Support',
        quantity: 1,
        unit_price: 2000,
      },
    ],
    notes: 'Price includes 12-month subscription, initial setup, device configuration, playlist curation assistance, and on-site training for staff.',
  },
  {
    id: 'beat-breeze-app-subscription',
    name: 'Beat Breeze App Subscription (12 months + Service)',
    title: 'Beat Breeze App Subscription - 12 Months',
    description: 'Smart music management system with 12-month subscription including professional setup and ongoing support.',
    items: [
      {
        description: 'Beat Breeze App Subscription (12 months)',
        quantity: 1,
        unit_price: 15000,
      },
      {
        description: 'Professional Setup and Integration Service',
        quantity: 1,
        unit_price: 5000,
      },
      {
        description: 'Monthly Support and Maintenance',
        quantity: 12,
        unit_price: 500,
      },
    ],
    notes: 'Includes full-feature app subscription, professional setup, system integration, and monthly support check-ins throughout the subscription period.',
  },
  {
    id: 'soundtrack-player-hardware',
    name: 'Soundtrack Player Hardware',
    title: 'Soundtrack Player Hardware Package',
    description: 'Complete hardware solution for professional background music playback with installation and warranty.',
    items: [
      {
        description: 'Soundtrack Player Device',
        quantity: 1,
        unit_price: 25000,
      },
      {
        description: 'Professional Installation Service',
        quantity: 1,
        unit_price: 5000,
      },
      {
        description: 'Extended Warranty (2 years)',
        quantity: 1,
        unit_price: 3000,
      },
      {
        description: 'Premium Audio Cables and Accessories',
        quantity: 1,
        unit_price: 2000,
      },
    ],
    notes: 'Hardware package includes player device, professional installation, 2-year extended warranty, and all necessary cables and mounting accessories.',
  },
  {
    id: 'beat-breeze-player-hardware',
    name: 'Beat Breeze Player Hardware',
    title: 'Beat Breeze Player Hardware Solution',
    description: 'Advanced music player hardware with smart features, professional installation, and comprehensive support package.',
    items: [
      {
        description: 'Beat Breeze Player Device (Latest Model)',
        quantity: 1,
        unit_price: 35000,
      },
      {
        description: 'Professional Installation and Configuration',
        quantity: 1,
        unit_price: 7000,
      },
      {
        description: 'Network Integration and Testing',
        quantity: 1,
        unit_price: 3000,
      },
      {
        description: 'Premium Support Package (1 year)',
        quantity: 1,
        unit_price: 5000,
      },
    ],
    notes: 'Complete hardware solution with latest Beat Breeze player, professional installation, network integration, and 1-year premium support with priority response.',
  },
];

// Predefined item options for custom selections
export const predefinedItems = {
  subscriptions: [
    {
      description: 'Soundtrack App Subscription (Monthly)',
      unit_price: 1200,
    },
    {
      description: 'Soundtrack App Subscription (6 months)',
      unit_price: 6500,
    },
    {
      description: 'Soundtrack App Subscription (12 months)',
      unit_price: 12000,
    },
    {
      description: 'Beat Breeze App Subscription (Monthly)',
      unit_price: 1500,
    },
    {
      description: 'Beat Breeze App Subscription (6 months)',
      unit_price: 8000,
    },
    {
      description: 'Beat Breeze App Subscription (12 months)',
      unit_price: 15000,
    },
  ],
  hardware: [
    {
      description: 'Soundtrack Player Device',
      unit_price: 25000,
    },
    {
      description: 'Beat Breeze Player Device (Latest Model)',
      unit_price: 35000,
    },
    {
      description: 'Player Mounting Bracket',
      unit_price: 1500,
    },
    {
      description: 'Premium Audio Cables Set',
      unit_price: 2000,
    },
    {
      description: 'Network Adapter for Player',
      unit_price: 3000,
    },
  ],
  services: [
    {
      description: 'Initial Setup and Configuration Service',
      unit_price: 3000,
    },
    {
      description: 'Professional Installation Service',
      unit_price: 5000,
    },
    {
      description: 'On-site Training (Half Day)',
      unit_price: 2000,
    },
    {
      description: 'On-site Training (Full Day)',
      unit_price: 3500,
    },
    {
      description: 'Network Integration and Testing',
      unit_price: 3000,
    },
    {
      description: 'Playlist Curation Service',
      unit_price: 5000,
    },
    {
      description: 'Monthly Support and Maintenance',
      unit_price: 500,
    },
    {
      description: 'Premium Support Package (1 year)',
      unit_price: 5000,
    },
    {
      description: 'Extended Warranty (1 year)',
      unit_price: 1500,
    },
    {
      description: 'Extended Warranty (2 years)',
      unit_price: 3000,
    },
  ],
};