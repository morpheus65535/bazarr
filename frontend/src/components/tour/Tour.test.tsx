import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { customRender, screen } from "@/tests";
import Tour, { TourStep } from "./Tour";

const steps: TourStep[] = [
  {
    id: "first",
    title: "First step",
    description: "First description",
  },
  {
    id: "second",
    title: "Second step",
    description: "Second description",
  },
];

describe("Tour", () => {
  it("renders nothing while closed", () => {
    customRender(<Tour opened={false} steps={steps} onFinish={vi.fn()}></Tour>);

    expect(
      screen.queryByTestId("onboarding-tour-title"),
    ).not.toBeInTheDocument();
  });

  it("walks forward through the steps and finishes on the last one", async () => {
    const onFinish = vi.fn();
    customRender(<Tour opened steps={steps} onFinish={onFinish}></Tour>);
    const user = userEvent.setup();

    expect(screen.getByTestId("onboarding-tour-title")).toHaveTextContent(
      "First step",
    );

    await user.keyboard("{ArrowRight}");

    expect(screen.getByTestId("onboarding-tour-title")).toHaveTextContent(
      "Second step",
    );

    await user.keyboard("{ArrowRight}");

    expect(onFinish).toHaveBeenCalledTimes(1);
  });

  it("walks back to the previous step", async () => {
    customRender(<Tour opened steps={steps} onFinish={vi.fn()}></Tour>);
    const user = userEvent.setup();

    await user.keyboard("{ArrowRight}");
    await user.keyboard("{ArrowLeft}");

    expect(screen.getByTestId("onboarding-tour-title")).toHaveTextContent(
      "First step",
    );
  });

  it("finishes when the tour is skipped", async () => {
    const onFinish = vi.fn();
    customRender(<Tour opened steps={steps} onFinish={onFinish}></Tour>);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Skip tour" }));

    expect(onFinish).toHaveBeenCalledTimes(1);
  });

  it("finishes when escape is pressed", async () => {
    const onFinish = vi.fn();
    customRender(<Tour opened steps={steps} onFinish={onFinish}></Tour>);
    const user = userEvent.setup();

    await user.keyboard("{Escape}");

    expect(onFinish).toHaveBeenCalledTimes(1);
  });

  it("starts from the provided step", () => {
    customRender(
      <Tour
        opened
        steps={steps}
        initialStepIndex={1}
        onFinish={vi.fn()}
      ></Tour>,
    );

    expect(screen.getByTestId("onboarding-tour-title")).toHaveTextContent(
      "Second step",
    );
  });

  it("clamps a resumed step beyond the last step", () => {
    customRender(
      <Tour
        opened
        steps={steps}
        initialStepIndex={9}
        onFinish={vi.fn()}
      ></Tour>,
    );

    expect(screen.getByTestId("onboarding-tour-title")).toHaveTextContent(
      "Second step",
    );
  });

  it("reports step changes", async () => {
    const onStepChange = vi.fn();
    customRender(
      <Tour
        opened
        steps={steps}
        onStepChange={onStepChange}
        onFinish={vi.fn()}
      ></Tour>,
    );
    const user = userEvent.setup();

    await user.keyboard("{ArrowRight}");

    expect(onStepChange).toHaveBeenCalledWith(1);
  });

  it("renders the step action controls", () => {
    const actionSteps: TourStep[] = [
      {
        id: "action",
        title: "Action step",
        description: "With controls",
        action: <button type="button">Do it</button>,
      },
    ];

    customRender(<Tour opened steps={actionSteps} onFinish={vi.fn()}></Tour>);

    expect(screen.getByRole("button", { name: "Do it" })).toBeInTheDocument();
  });

  it("ignores navigation keys while typing in a field", async () => {
    const actionSteps: TourStep[] = [
      {
        id: "action",
        title: "Action step",
        description: "With controls",
        action: <input aria-label="Field" />,
      },
      {
        id: "action-two",
        title: "Second step",
        description: "Second",
      },
    ];

    customRender(<Tour opened steps={actionSteps} onFinish={vi.fn()}></Tour>);
    const user = userEvent.setup();

    await user.click(screen.getByLabelText("Field"));
    await user.keyboard("{ArrowRight}");

    expect(screen.getByTestId("onboarding-tour-title")).toHaveTextContent(
      "Action step",
    );
  });

  it("blocks forward navigation while a step is blocked", async () => {
    const blockedSteps: TourStep[] = [
      {
        id: "gate",
        title: "Requirement",
        description: "Must enable one",
        isBlocked: true,
        blockedMessage: "Enable one to continue",
      },
      {
        id: "after",
        title: "After gate",
        description: "Next step",
      },
    ];

    customRender(<Tour opened steps={blockedSteps} onFinish={vi.fn()}></Tour>);
    const user = userEvent.setup();

    expect(screen.getByText("Enable one to continue")).toBeInTheDocument();

    await user.keyboard("{ArrowRight}");

    expect(screen.getByTestId("onboarding-tour-title")).toHaveTextContent(
      "Requirement",
    );
  });

  it("advances after the targeted control is clicked", async () => {
    const autoSteps: TourStep[] = [
      {
        id: "first",
        title: "First",
        description: "Click it",
        target: '[data-testid="go-target"]',
        advanceOnAction: "primary",
      },
      {
        id: "second",
        title: "Second",
        description: "Next",
      },
    ];

    customRender(
      <div>
        <button type="button" data-testid="go-target">
          Go
        </button>
        <Tour opened steps={autoSteps} onFinish={vi.fn()}></Tour>
      </div>,
    );
    const user = userEvent.setup();

    await screen.findByTestId("onboarding-highlight");

    await user.click(screen.getByTestId("go-target"));

    expect(await screen.findByText("Second")).toBeInTheDocument();
  });

  it("advances on settings-saved for secondary steps", async () => {
    const saveSteps: TourStep[] = [
      {
        id: "first",
        title: "First",
        description: "Save it",
        advanceOnAction: "secondary",
      },
      {
        id: "second",
        title: "Second",
        description: "Next",
      },
    ];

    customRender(<Tour opened steps={saveSteps} onFinish={vi.fn()}></Tour>);

    window.dispatchEvent(new Event("bazarr-settings-saved"));

    expect(await screen.findByText("Second")).toBeInTheDocument();
  });

  it("skips steps that are already fulfilled", async () => {
    const fulfilledSteps: TourStep[] = [
      {
        id: "done-already",
        title: "Already done",
        description: "Fulfilled",
        isFulfilled: true,
      },
      {
        id: "second",
        title: "Second step",
        description: "Next",
      },
    ];

    customRender(
      <Tour opened steps={fulfilledSteps} onFinish={vi.fn()}></Tour>,
    );

    expect(await screen.findByText("Second step")).toBeInTheDocument();
  });

  it("offers a skip-this-step button on optional steps", async () => {
    const optionalSteps: TourStep[] = [
      {
        id: "opt",
        title: "Optional step",
        description: "Optional",
        optional: true,
      },
      {
        id: "next",
        title: "Second step",
        description: "Next",
      },
    ];

    customRender(<Tour opened steps={optionalSteps} onFinish={vi.fn()}></Tour>);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Skip this step" }));

    expect(await screen.findByText("Second step")).toBeInTheDocument();
  });

  it("advances once a marker element appears", async () => {
    const markerSteps: TourStep[] = [
      {
        id: "first",
        title: "First",
        description: "Waiting",
        advanceWhenPresent: '[data-testid="marker"]',
      },
      {
        id: "second",
        title: "Second",
        description: "Next",
      },
    ];

    customRender(
      <div>
        <span data-testid="marker" />
        <Tour opened steps={markerSteps} onFinish={vi.fn()}></Tour>
      </div>,
    );

    expect(await screen.findByText("Second")).toBeInTheDocument();
  });

  it("spotlights a matching target element", async () => {
    const targetSteps: TourStep[] = [
      {
        id: "target",
        title: "Targeted step",
        description: "Points at an element",
        target: '[data-testid="tour-target"]',
      },
    ];

    customRender(
      <>
        <div data-testid="tour-target">Anchor</div>
        <Tour opened steps={targetSteps} onFinish={vi.fn()}></Tour>
      </>,
    );

    expect(
      await screen.findByTestId("onboarding-highlight"),
    ).toBeInTheDocument();
  });
});
