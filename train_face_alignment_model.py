"""
Train alignment model from annotated top-view images.

This trains only face geometry (quads), not color classification.
"""

import argparse

from face_alignment_model import FaceAlignmentModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train cube face alignment model")
    parser.add_argument(
        "--images-dir",
        type=str,
        default="training_data/CubeStates",
        help="Directory containing annotated source images",
    )
    parser.add_argument(
        "--annotations-dir",
        type=str,
        default=None,
        help="Directory containing annotation JSONs (default: <images-dir>/annotations)",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="face_alignment_model.pkl",
        help="Output path for the trained alignment model",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=5,
        help="Minimum annotated samples required for training",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluate model against annotations after training/loading",
    )
    parser.add_argument(
        "--evaluate-only",
        action="store_true",
        help="Skip training and only evaluate an existing model",
    )
    parser.add_argument(
        "--overlays-dir",
        type=str,
        default="training_data/CubeStates/eval_overlays",
        help="Directory to save evaluation overlay images",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="How many worst images to print in evaluation summary",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    model = FaceAlignmentModel(model_path=args.model_path)
    if args.evaluate_only:
        if not model.load():
            raise FileNotFoundError(
                f"Could not load model at {args.model_path}. Train first or provide valid --model-path."
            )
        print(f"Loaded model: {args.model_path}")
    else:
        metrics = model.train_from_annotations(
            images_dir=args.images_dir,
            annotations_dir=args.annotations_dir,
            min_samples=args.min_samples,
        )
        model.save()
        print("\nAlignment model trained successfully.")
        print(f"Saved model: {args.model_path}")
        print(f"Samples used: {int(metrics['samples'])}")
        print(f"Train RMSE (normalized coords): {metrics['train_rmse_norm']:.5f}")
        print("Note: lower is better; this is geometry-only training.")

    if args.evaluate or args.evaluate_only:
        eval_metrics = model.evaluate_annotations(
            images_dir=args.images_dir,
            annotations_dir=args.annotations_dir,
            overlays_dir=args.overlays_dir,
        )
        print("\nEvaluation summary")
        print(f"Samples: {eval_metrics['samples']}")
        print(f"Mean point error: {eval_metrics['mean_error_px']:.2f}px")
        print(f"Median point error: {eval_metrics['median_error_px']:.2f}px")
        print(f"Max point error: {eval_metrics['max_error_px']:.2f}px")
        print(f"Saved overlays: {args.overlays_dir}")

        print("\nWorst samples:")
        for row in eval_metrics["per_image"][: max(1, args.top_k)]:
            print(f"  {row['image_file']}: {row['mean_point_error_px']:.2f}px")


if __name__ == "__main__":
    main()
