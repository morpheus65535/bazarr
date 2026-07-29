import { faWrench } from "@fortawesome/free-solid-svg-icons";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { Action } from "@/components";
import { customRender, fireEvent, screen } from "@/tests";
import PosterCard from "./PosterCard";

describe("PosterCard", () => {
  it("renders the poster image, title and year", () => {
    customRender(
      <PosterCard
        title="My Show"
        year="2020"
        poster="/images/series/MediaCover/1/poster-250.jpg"
        to="/series/1"
      ></PosterCard>,
    );

    expect(screen.getByRole("img", { name: "My Show" })).toBeInTheDocument();
    expect(screen.getByText("My Show")).toBeInTheDocument();
    expect(screen.getByText("2020")).toBeInTheDocument();
  });

  it("links to the item detail page", () => {
    customRender(
      <PosterCard title="My Show" poster={null} to="/series/1"></PosterCard>,
    );

    expect(screen.getByRole("link", { name: "My Show" })).toHaveAttribute(
      "href",
      "/series/1",
    );
  });

  it("renders a placeholder when the poster is missing", () => {
    customRender(
      <PosterCard title="My Show" poster={null} to="/series/1"></PosterCard>,
    );

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("falls back to the placeholder when the image fails to load", () => {
    customRender(
      <PosterCard
        title="My Show"
        poster="/images/series/broken.jpg"
        to="/series/1"
      ></PosterCard>,
    );

    fireEvent.error(screen.getByRole("img", { name: "My Show" }));

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("renders header, actions and overlay content", async () => {
    const onEdit = vitest.fn();

    customRender(
      <PosterCard
        title="My Show"
        poster={null}
        to="/series/1"
        header={<span>status icons</span>}
        actions={
          <Action label="Edit Series" icon={faWrench} onClick={onEdit} />
        }
      >
        <span>progress</span>
      </PosterCard>,
    );

    expect(screen.getByText("status icons")).toBeInTheDocument();
    expect(screen.getByText("progress")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Edit Series" }));

    expect(onEdit).toHaveBeenCalledTimes(1);
  });
});
